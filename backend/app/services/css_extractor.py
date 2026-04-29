import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Tuple
import re
from app.models.schemas import CSSRule, CSSSourceType

class CSSExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def extract_from_url(self, url: str, options: Dict = None) -> Tuple[List[CSSRule], List[Dict]]:
        if options is None:
            options = {"include_inline": True, "include_external": True, "deep_analysis": True}
        
        all_rules = []
        css_sources = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = response.url
            
            if options.get("include_external", True):
                external_rules, external_sources = self._extract_external_css(soup, base_url)
                all_rules.extend(external_rules)
                css_sources.extend(external_sources)
            
            style_tags = soup.find_all('style')
            for style_tag in style_tags:
                css_content = style_tag.string or ''
                if css_content:
                    rules = self._parse_css_content(css_content, CSSSourceType.STYLE_TAG, "embedded_style")
                    all_rules.extend(rules)
                    css_sources.append({
                        "type": CSSSourceType.STYLE_TAG.value,
                        "source": "embedded_style",
                        "rules_count": len(rules)
                    })
            
            if options.get("include_inline", True):
                inline_rules = self._extract_inline_styles(soup, url)
                all_rules.extend(inline_rules)
                if inline_rules:
                    css_sources.append({
                        "type": CSSSourceType.INLINE.value,
                        "source": "inline_styles",
                        "rules_count": len(inline_rules)
                    })
        
        except Exception as e:
            print(f"Error extracting CSS from {url}: {e}")
        
        return all_rules, css_sources

    def _extract_external_css(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[CSSRule], List[Dict]]:
        all_rules = []
        sources = []
        
        link_tags = soup.find_all('link', rel='stylesheet')
        for link in link_tags:
            href = link.get('href')
            if not href:
                continue
            
            css_url = urljoin(base_url, href)
            try:
                response = self.session.get(css_url, timeout=30)
                response.raise_for_status()
                css_content = response.text
                
                rules = self._parse_css_content(css_content, CSSSourceType.EXTERNAL, css_url)
                all_rules.extend(rules)
                
                sources.append({
                    "type": CSSSourceType.EXTERNAL.value,
                    "source": css_url,
                    "rules_count": len(rules),
                    "size_bytes": len(css_content)
                })
            except Exception as e:
                print(f"Error fetching CSS from {css_url}: {e}")
                continue
        
        return all_rules, sources

    def _extract_inline_styles(self, soup: BeautifulSoup, base_url: str) -> List[CSSRule]:
        rules = []
        elements_with_style = soup.find_all(style=True)
        
        for elem in elements_with_style:
            style_content = elem.get('style', '')
            if not style_content:
                continue
            
            tag_name = elem.name
            classes = elem.get('class', [])
            id_attr = elem.get('id')
            
            selector = tag_name
            if id_attr:
                selector += f"#{id_attr}"
            for cls in classes:
                selector += f".{cls}"
            
            declarations = self._parse_inline_style_declarations(style_content)
            
            if declarations:
                rule = CSSRule(
                    selector=selector,
                    declarations=declarations,
                    specificity=self._calculate_specificity(selector),
                    source_type=CSSSourceType.INLINE,
                    source_file=base_url
                )
                rules.append(rule)
        
        return rules

    def _parse_inline_style_declarations(self, style_content: str) -> Dict[str, str]:
        declarations = {}
        if not style_content:
            return declarations
        
        pairs = style_content.split(';')
        for pair in pairs:
            pair = pair.strip()
            if ':' in pair:
                key, value = pair.split(':', 1)
                declarations[key.strip()] = value.strip()
        
        return declarations

    def _parse_css_content(self, css_content: str, source_type: CSSSourceType, source_file: str) -> List[CSSRule]:
        rules = []
        
        css_content = self._remove_css_comments(css_content)
        rule_blocks = self._extract_rule_blocks(css_content)
        
        for selector_str, declarations_str, line_num in rule_blocks:
            selectors = [s.strip() for s in selector_str.split(',') if s.strip()]
            
            declarations = self._parse_declarations(declarations_str)
            
            for selector in selectors:
                if declarations:
                    rule = CSSRule(
                        selector=selector,
                        declarations=declarations,
                        specificity=self._calculate_specificity(selector),
                        source_type=source_type,
                        source_file=source_file,
                        line_number=line_num
                    )
                    rules.append(rule)
        
        return rules

    def _remove_css_comments(self, css_content: str) -> str:
        import re
        return re.sub(r'/\*[\s\S]*?\*/', '', css_content)

    def _extract_rule_blocks(self, css_content: str) -> List[Tuple[str, str, int]]:
        blocks = []
        lines = css_content.split('\n')
        current_selector = ""
        current_declarations = ""
        in_block = False
        brace_count = 0
        line_num = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            line = line.strip()
            
            if not line:
                continue
            
            if not in_block:
                if '{' in line:
                    parts = line.split('{', 1)
                    current_selector = parts[0].strip()
                    if len(parts) > 1:
                        remaining = parts[1]
                        if '}' in remaining:
                            current_declarations = remaining.split('}')[0].strip()
                            if current_selector and current_declarations:
                                blocks.append((current_selector, current_declarations, line_num))
                            current_selector = ""
                            current_declarations = ""
                        else:
                            current_declarations = remaining.strip()
                            in_block = True
                            brace_count = 1
                continue
            
            current_declarations += " " + line
            
            for char in line:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        current_declarations = current_declarations.rsplit('}', 1)[0].strip()
                        if current_selector and current_declarations:
                            blocks.append((current_selector, current_declarations, line_num))
                        current_selector = ""
                        current_declarations = ""
                        in_block = False
                        break
        
        return blocks

    def _parse_declarations(self, declarations_str: str) -> Dict[str, str]:
        declarations = {}
        if not declarations_str:
            return declarations
        
        pairs = declarations_str.split(';')
        for pair in pairs:
            pair = pair.strip()
            if ':' in pair and not pair.startswith('@'):
                try:
                    key, value = pair.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        declarations[key] = value
                except:
                    continue
        
        return declarations

    def _calculate_specificity(self, selector: str) -> float:
        id_count = selector.count('#')
        class_count = selector.count('.')
        attr_count = len(re.findall(r'\[[^\]]+\]', selector))
        pseudo_class_count = len(re.findall(r':(?:hover|focus|active|visited|link|first-child|last-child|nth-child|nth-of-type|first-of-type|last-of-type|only-child|only-of-type|empty|enabled|disabled|checked|required|optional)', selector, re.IGNORECASE))
        
        tag_count = len(re.findall(r'(^|\s|\+|>|\~)([a-zA-Z][a-zA-Z0-9\-]*)(?![^{]*\})', selector))
        pseudo_elem_count = len(re.findall(r'::(?:before|after|first-letter|first-line|selection)', selector))
        
        specificity = (
            id_count * 1000 +
            (class_count + attr_count + pseudo_class_count) * 100 +
            (tag_count + pseudo_elem_count) * 10
        ) / 1000.0
        
        return specificity
