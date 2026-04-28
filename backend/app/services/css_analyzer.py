from typing import List, Dict, Tuple, Set
from collections import defaultdict
import re
from app.models.schemas import (
    CSSRule, CSSClassNode, CSSEdge, CSSGraphData,
    RedundantItem, OptimizationSuggestion
)

class CSSAnalyzer:
    def __init__(self):
        self.class_nodes: Dict[str, CSSClassNode] = {}
        self.edges: List[CSSEdge] = []
        self.color_usage: Dict[str, List[Dict]] = defaultdict(list)
        self.value_usage: Dict[str, List[Dict]] = defaultdict(list)
        self.duplicate_selectors: Dict[str, List[CSSRule]] = defaultdict(list)
        self.property_usage: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))

    def analyze(self, rules: List[CSSRule]) -> Tuple[CSSGraphData, List[RedundantItem], List[OptimizationSuggestion], Dict]:
        self._reset_state()
        
        for rule in rules:
            self._process_rule(rule)
        
        self._build_relationships()
        self._calculate_specificity_hierarchy()
        
        graph_data = CSSGraphData(
            nodes=list(self.class_nodes.values()),
            edges=self.edges
        )
        
        redundant_items = self._find_redundant_items()
        optimization_suggestions = self._generate_optimization_suggestions()
        statistics = self._generate_statistics()
        
        return graph_data, redundant_items, optimization_suggestions, statistics

    def _reset_state(self):
        self.class_nodes = {}
        self.edges = []
        self.color_usage = defaultdict(list)
        self.value_usage = defaultdict(list)
        self.duplicate_selectors = defaultdict(list)
        self.property_usage = defaultdict(lambda: defaultdict(list))

    def _process_rule(self, rule: CSSRule):
        selector = rule.selector
        
        self.duplicate_selectors[selector].append(rule)
        
        classes = self._extract_classes_from_selector(selector)
        
        for cls in classes:
            if cls not in self.class_nodes:
                self.class_nodes[cls] = CSSClassNode(
                    id=cls,
                    name=cls,
                    type="class",
                    rules=[],
                    properties={},
                    parent_classes=[],
                    child_classes=[],
                    specificity=0.0
                )
            self.class_nodes[cls].rules.append(rule)
            if rule.specificity > self.class_nodes[cls].specificity:
                self.class_nodes[cls].specificity = rule.specificity
        
        for prop, value in rule.declarations.items():
            self.property_usage[prop][value].append({
                "selector": selector,
                "source_file": rule.source_file,
                "line_number": rule.line_number
            })
            
            if self._is_color_value(value):
                normalized_color = self._normalize_color(value)
                self.color_usage[normalized_color].append({
                    "selector": selector,
                    "property": prop,
                    "value": value,
                    "source_file": rule.source_file,
                    "line_number": rule.line_number
                })
            
            if self._is_size_value(value):
                self.value_usage[f"{prop}:{value}"].append({
                    "selector": selector,
                    "property": prop,
                    "value": value,
                    "source_file": rule.source_file,
                    "line_number": rule.line_number
                })

    def _extract_classes_from_selector(self, selector: str) -> Set[str]:
        classes = set()
        
        class_pattern = r'\.([a-zA-Z_][a-zA-Z0-9_\-]*)'
        matches = re.findall(class_pattern, selector)
        for match in matches:
            classes.add(f".{match}")
        
        return classes

    def _build_relationships(self):
        for rule in self._get_all_rules():
            selector = rule.selector
            classes = self._extract_classes_from_selector(selector)
            
            descendant_pattern = r'(\.[a-zA-Z_][a-zA-Z0-9_\-]*)\s+(\.[a-zA-Z_][a-zA-Z0-9_\-]*)'
            for match in re.finditer(descendant_pattern, selector):
                parent, child = match.groups()
                parent = f".{parent}" if not parent.startswith('.') else parent
                child = f".{child}" if not child.startswith('.') else child
                self._add_edge(parent, child, "descendant")
            
            child_pattern = r'(\.[a-zA-Z_][a-zA-Z0-9_\-]*)\s*>\s*(\.[a-zA-Z_][a-zA-Z0-9_\-]*)'
            for match in re.finditer(child_pattern, selector):
                parent, child = match.groups()
                parent = f".{parent}" if not parent.startswith('.') else parent
                child = f".{child}" if not child.startswith('.') else child
                self._add_edge(parent, child, "direct-child")
            
            sibling_pattern = r'(\.[a-zA-Z_][a-zA-Z0-9_\-]*)\s*[\+~]\s*(\.[a-zA-Z_][a-zA-Z0-9_\-]*)'
            for match in re.finditer(sibling_pattern, selector):
                first, second = match.groups()
                first = f".{first}" if not first.startswith('.') else first
                second = f".{second}" if not second.startswith('.') else second
                self._add_edge(first, second, "sibling")
            
            combined_pattern = r'(\.[a-zA-Z_][a-zA-Z0-9_\-]*)(\.[a-zA-Z_][a-zA-Z0-9_\-]+)'
            for match in re.finditer(combined_pattern, selector):
                base = match.group(1)
                modifiers = match.group(2)
                base = f".{base}" if not base.startswith('.') else base
                for modifier in re.findall(r'\.[a-zA-Z_][a-zA-Z0-9_\-]*', modifiers):
                    self._add_edge(base, f"{base}{modifier}", "modifier")

    def _add_edge(self, source: str, target: str, edge_type: str):
        if source in self.class_nodes and target in self.class_nodes:
            edge_id = f"{source}-{target}-{edge_type}"
            
            if not any(e.id == edge_id for e in self.edges):
                self.edges.append(CSSEdge(
                    id=edge_id,
                    source=source,
                    target=target,
                    type=edge_type,
                    strength=1.0
                ))
                
                if target not in self.class_nodes[source].child_classes:
                    self.class_nodes[source].child_classes.append(target)
                if source not in self.class_nodes[target].parent_classes:
                    self.class_nodes[target].parent_classes.append(source)

    def _calculate_specificity_hierarchy(self):
        for node_id, node in self.class_nodes.items():
            inherited_props = {}
            for parent_id in node.parent_classes:
                if parent_id in self.class_nodes:
                    parent_node = self.class_nodes[parent_id]
                    for rule in parent_node.rules:
                        for prop, value in rule.declarations.items():
                            if self._is_inheritable_property(prop):
                                if prop not in inherited_props:
                                    inherited_props[prop] = {
                                        "value": value,
                                        "source": parent_id,
                                        "specificity": rule.specificity
                                    }
            
            node.properties["inherited"] = inherited_props

    def _is_inheritable_property(self, prop: str) -> bool:
        inheritable = {
            "color", "font-family", "font-size", "font-weight", "font-style",
            "line-height", "text-align", "text-indent", "text-transform",
            "letter-spacing", "word-spacing", "direction", "visibility",
            "cursor", "list-style-type", "list-style-position", "list-style-image",
            "quotes", "border-collapse", "border-spacing", "caption-side",
            "empty-cells", "table-layout"
        }
        return prop.lower() in inheritable

    def _is_color_value(self, value: str) -> bool:
        value = value.strip().lower()
        
        if value.startswith('#') and len(value) in (4, 7, 9):
            return True
        
        if value.startswith('rgb(') or value.startswith('rgba('):
            return True
        
        if value.startswith('hsl(') or value.startswith('hsla('):
            return True
        
        named_colors = {
            "transparent", "currentcolor", "aliceblue", "antiquewhite", "aqua",
            "aquamarine", "azure", "beige", "bisque", "black", "blanchedalmond",
            "blue", "blueviolet", "brown", "burlywood", "cadetblue", "chartreuse",
            "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan",
            "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen",
            "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid",
            "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategray",
            "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray",
            "dodgerblue", "firebrick", "floralwhite", "forestgreen", "fuchsia",
            "gainsboro", "ghostwhite", "gold", "goldenrod", "gray", "green",
            "greenyellow", "honeydew", "hotpink", "indianred", "indigo", "ivory",
            "khaki", "lavender", "lavenderblush", "lawngreen", "lemonchiffon",
            "lightblue", "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray",
            "lightgreen", "lightpink", "lightsalmon", "lightseagreen", "lightskyblue",
            "lightslategray", "lightsteelblue", "lightyellow", "lime", "limegreen",
            "linen", "magenta", "maroon", "mediumaquamarine", "mediumblue",
            "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue",
            "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue",
            "mintcream", "mistyrose", "moccasin", "navajowhite", "navy", "oldlace",
            "olive", "olivedrab", "orange", "orangered", "orchid", "palegoldenrod",
            "palegreen", "paleturquoise", "palevioletred", "papayawhip", "peachpuff",
            "peru", "pink", "plum", "powderblue", "purple", "rebeccapurple", "red",
            "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown", "seagreen",
            "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray", "snow",
            "springgreen", "steelblue", "tan", "teal", "thistle", "tomato", "turquoise",
            "violet", "wheat", "white", "whitesmoke", "yellow", "yellowgreen"
        }
        return value in named_colors

    def _normalize_color(self, value: str) -> str:
        return value.strip().lower()

    def _is_size_value(self, value: str) -> bool:
        value = value.strip().lower()
        
        size_units = ['px', 'em', 'rem', '%', 'vh', 'vw', 'vmin', 'vmax', 'pt', 'pc', 'in', 'cm', 'mm']
        for unit in size_units:
            if value.endswith(unit):
                return True
        
        try:
            float(value)
            return True
        except ValueError:
            pass
        
        return False

    def _get_all_rules(self) -> List[CSSRule]:
        rules = []
        for node in self.class_nodes.values():
            rules.extend(node.rules)
        return rules

    def _find_redundant_items(self) -> List[RedundantItem]:
        redundant_items = []
        
        for color, locations in self.color_usage.items():
            if len(locations) >= 3:
                redundant_items.append(RedundantItem(
                    type="duplicate-color",
                    value=color,
                    locations=locations,
                    suggestion=f"Consider defining a CSS variable for color '{color}' used {len(locations)} times"
                ))
        
        for key, locations in self.value_usage.items():
            if len(locations) >= 3:
                prop, value = key.split(':', 1)
                redundant_items.append(RedundantItem(
                    type="duplicate-value",
                    value=f"{prop}: {value}",
                    locations=locations,
                    suggestion=f"Consider creating a utility class for '{prop}: {value}' used {len(locations)} times"
                ))
        
        for selector, rules in self.duplicate_selectors.items():
            if len(rules) > 1:
                declarations_list = []
                for rule in rules:
                    declarations_list.append({
                        "declarations": rule.declarations,
                        "source_file": rule.source_file,
                        "line_number": rule.line_number
                    })
                
                redundant_items.append(RedundantItem(
                    type="duplicate-selector",
                    value=selector,
                    locations=declarations_list,
                    suggestion=f"Selector '{selector}' is defined {len(rules)} times. Consider merging these rules."
                ))
        
        return redundant_items

    def _generate_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        suggestions = []
        
        total_nodes = len(self.class_nodes)
        if total_nodes > 0:
            nodes_without_parents = sum(1 for node in self.class_nodes.values() if not node.parent_classes)
            orphan_ratio = nodes_without_parents / total_nodes
            
            if orphan_ratio > 0.8:
                suggestions.append(OptimizationSuggestion(
                    category="architecture",
                    issue="High number of orphan classes",
                    severity="medium",
                    suggestion=f"{nodes_without_parents} out of {total_nodes} classes have no parent relationships. Consider using a more structured naming convention like BEM.",
                    affected_items=[node.name for node in self.class_nodes.values() if not node.parent_classes][:10]
                ))
        
        deep_nodes = []
        for node_id, node in self.class_nodes.items():
            depth = self._calculate_node_depth(node_id)
            if depth > 4:
                deep_nodes.append(node.name)
        
        if deep_nodes:
            suggestions.append(OptimizationSuggestion(
                category="specificity",
                issue="Deep selector nesting detected",
                severity="high",
                suggestion=f"Some selectors have nesting depth greater than 4. This increases specificity and makes maintenance harder.",
                affected_items=deep_nodes[:10]
            ))
        
        color_count = len(self.color_usage)
        if color_count > 20:
            suggestions.append(OptimizationSuggestion(
                category="consistency",
                issue="Too many distinct colors",
                severity="medium",
                suggestion=f"You're using {color_count} distinct colors. Consider reducing this to create a more consistent design system.",
                affected_items=list(self.color_usage.keys())[:10]
            ))
        
        return suggestions

    def _calculate_node_depth(self, node_id: str, visited: Set[str] = None) -> int:
        if visited is None:
            visited = set()
        
        if node_id in visited:
            return 0
        visited.add(node_id)
        
        if node_id not in self.class_nodes:
            return 0
        
        node = self.class_nodes[node_id]
        if not node.parent_classes:
            return 1
        
        max_depth = 0
        for parent_id in node.parent_classes:
            depth = self._calculate_node_depth(parent_id, visited.copy())
            max_depth = max(max_depth, depth)
        
        return max_depth + 1

    def _generate_statistics(self) -> Dict:
        stats = {
            "total_classes": len(self.class_nodes),
            "total_relationships": len(self.edges),
            "unique_colors": len(self.color_usage),
            "color_usage_count": sum(len(locs) for locs in self.color_usage.values()),
            "average_depth": 0,
            "max_depth": 0,
            "orphan_classes": 0,
            "leaf_classes": 0
        }
        
        depths = []
        for node_id in self.class_nodes.keys():
            depth = self._calculate_node_depth(node_id)
            depths.append(depth)
            
            if not self.class_nodes[node_id].parent_classes:
                stats["orphan_classes"] += 1
            if not self.class_nodes[node_id].child_classes:
                stats["leaf_classes"] += 1
        
        if depths:
            stats["average_depth"] = sum(depths) / len(depths)
            stats["max_depth"] = max(depths)
        
        return stats
