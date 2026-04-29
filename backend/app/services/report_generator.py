from typing import Dict, Any, Optional
from app.models.schemas import CSSAnalysisResult
import json
from datetime import datetime

class ReportGenerator:
    def __init__(self):
        pass

    def generate_report(self, analysis_result: CSSAnalysisResult, format: str = "html") -> Dict[str, Any]:
        if format == "json":
            return self._generate_json_report(analysis_result)
        elif format == "html":
            return self._generate_html_report(analysis_result)
        else:
            return self._generate_json_report(analysis_result)

    def _generate_json_report(self, analysis_result: CSSAnalysisResult) -> Dict[str, Any]:
        return {
            "report_type": "css_analysis",
            "generated_at": datetime.now().isoformat(),
            "url": analysis_result.url,
            "summary": {
                "total_rules": analysis_result.total_rules,
                "total_classes": analysis_result.total_classes,
                "total_selectors": analysis_result.total_selectors,
                "css_sources_count": len(analysis_result.css_sources),
                "redundant_items_count": len(analysis_result.redundant_items),
                "suggestions_count": len(analysis_result.optimization_suggestions)
            },
            "css_sources": analysis_result.css_sources,
            "statistics": analysis_result.statistics,
            "redundant_items": [item.model_dump() for item in analysis_result.redundant_items],
            "optimization_suggestions": [item.model_dump() for item in analysis_result.optimization_suggestions],
            "graph_data": {
                "nodes_count": len(analysis_result.graph_data.nodes),
                "edges_count": len(analysis_result.graph_data.edges)
            }
        }

    def _generate_html_report(self, analysis_result: CSSAnalysisResult) -> Dict[str, Any]:
        html_content = self._build_html_content(analysis_result)
        
        return {
            "format": "html",
            "content": html_content,
            "filename": f"css_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        }

    def _build_html_content(self, analysis_result: CSSAnalysisResult) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Analysis Report - {analysis_result.url}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header .url {{ font-size: 14px; opacity: 0.9; word-break: break-all; }}
        .header .timestamp {{ font-size: 12px; opacity: 0.7; margin-top: 5px; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ font-size: 18px; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .stat-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .card {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }}
        .card-header {{ background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }}
        .card-title {{ font-weight: 600; }}
        .card-badge {{ background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .card-badge.warning {{ background: #ffc107; color: #333; }}
        .card-badge.danger {{ background: #dc3545; }}
        .card-badge.info {{ background: #17a2b8; }}
        .card-body {{ padding: 20px; }}
        .item-list {{ list-style: none; }}
        .item-list li {{ padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
        .item-list li:last-child {{ border-bottom: none; }}
        .item-value {{ font-family: monospace; background: #f8f9fa; padding: 2px 8px; border-radius: 4px; }}
        .location-list {{ margin-top: 10px; padding-left: 20px; font-size: 13px; color: #666; }}
        .location-list li {{ padding: 4px 0; border: none; }}
        .suggestion-card {{ border-left: 4px solid #667eea; }}
        .severity-high {{ border-left-color: #dc3545; }}
        .severity-medium {{ border-left-color: #ffc107; }}
        .severity-low {{ border-left-color: #28a745; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; font-size: 13px; }}
        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e0e0e0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 CSS Analysis Report</h1>
            <div class="url">Analyzed URL: {analysis_result.url}</div>
            <div class="timestamp">Generated at: {now}</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Overview</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{analysis_result.total_rules}</div>
                        <div class="stat-label">Total CSS Rules</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis_result.total_classes}</div>
                        <div class="stat-label">CSS Classes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(analysis_result.css_sources)}</div>
                        <div class="stat-label">CSS Sources</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(analysis_result.redundant_items)}</div>
                        <div class="stat-label">Redundancies Found</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📈 Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{analysis_result.statistics.get('unique_colors', 0)}</div>
                        <div class="stat-label">Unique Colors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis_result.statistics.get('average_depth', 0):.1f}</div>
                        <div class="stat-label">Avg Nesting Depth</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis_result.statistics.get('max_depth', 0)}</div>
                        <div class="stat-label">Max Nesting Depth</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis_result.statistics.get('orphan_classes', 0)}</div>
                        <div class="stat-label">Orphan Classes</div>
                    </div>
                </div>
            </div>
"""

        if analysis_result.redundant_items:
            html += """
            <div class="section">
                <h2>⚠️ Redundancies Found</h2>
"""
            for item in analysis_result.redundant_items:
                badge_class = "warning"
                if item.type == "duplicate-selector":
                    badge_class = "danger"
                elif item.type == "duplicate-color":
                    badge_class = "info"
                
                html += f"""
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">{item.type.replace('-', ' ').title()}</span>
                        <span class="card-badge {badge_class}">{len(item.locations)} occurrences</span>
                    </div>
                    <div class="card-body">
                        <p><strong>Value:</strong> <code class="item-value">{item.value}</code></p>
                        {f'<p><strong>Suggestion:</strong> {item.suggestion}</p>' if item.suggestion else ''}
                        <ul class="location-list">
"""
                for loc in item.locations[:5]:
                    source = loc.get('source_file', 'unknown')
                    line = loc.get('line_number', 'N/A')
                    selector = loc.get('selector', '')
                    html += f'                            <li>• {selector} @ {source}:{line}</li>\n'
                
                if len(item.locations) > 5:
                    html += f'                            <li>... and {len(item.locations) - 5} more</li>\n'
                
                html += """                        </ul>
                    </div>
                </div>
"""
            html += "            </div>\n"

        if analysis_result.optimization_suggestions:
            html += """
            <div class="section">
                <h2>💡 Optimization Suggestions</h2>
"""
            for suggestion in analysis_result.optimization_suggestions:
                severity_class = f"severity-{suggestion.severity}"
                html += f"""
                <div class="card suggestion-card {severity_class}">
                    <div class="card-header">
                        <span class="card-title">[{suggestion.category.upper()}] {suggestion.issue}</span>
                        <span class="card-badge {'danger' if suggestion.severity == 'high' else 'warning' if suggestion.severity == 'medium' else ''}">{suggestion.severity.upper()}</span>
                    </div>
                    <div class="card-body">
                        <p><strong>Suggestion:</strong> {suggestion.suggestion}</p>
                        {f'<p><strong>Affected items:</strong> {", ".join(suggestion.affected_items)}</p>' if suggestion.affected_items else ''}
                    </div>
                </div>
"""
            html += "            </div>\n"

        if analysis_result.css_sources:
            html += """
            <div class="section">
                <h2>📁 CSS Sources</h2>
"""
            for source in analysis_result.css_sources:
                source_type = source.get('type', 'unknown')
                html += f"""
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">{source_type.upper()}</span>
                        <span class="card-badge">{source.get('rules_count', 0)} rules</span>
                    </div>
                    <div class="card-body">
                        <p><strong>Source:</strong> <code class="item-value">{source.get('source', 'N/A')}</code></p>
                        {f'<p><strong>Size:</strong> {source.get("size_bytes", 0)} bytes</p>' if 'size_bytes' in source else ''}
                    </div>
                </div>
"""
            html += "            </div>\n"

        html += f"""
        </div>
        <div class="footer">
            <p>Generated by StyleLens CSS Analysis Tool</p>
            <p>Graph: {len(analysis_result.graph_data.nodes)} nodes, {len(analysis_result.graph_data.edges)} relationships</p>
        </div>
    </div>
</body>
</html>
"""
        return html
