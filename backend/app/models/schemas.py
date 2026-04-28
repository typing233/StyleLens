from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class CSSSourceType(str, Enum):
    INLINE = "inline"
    EXTERNAL = "external"
    STYLE_TAG = "style_tag"

class CSSRule(BaseModel):
    selector: str
    declarations: Dict[str, str]
    specificity: float
    source_type: CSSSourceType
    source_file: Optional[str] = None
    line_number: Optional[int] = None

class CSSClassNode(BaseModel):
    id: str
    name: str
    type: str = "class"
    rules: List[CSSRule] = []
    properties: Dict[str, Any] = {}
    parent_classes: List[str] = []
    child_classes: List[str] = []
    specificity: float = 0.0

class CSSEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    strength: float

class CSSGraphData(BaseModel):
    nodes: List[CSSClassNode]
    edges: List[CSSEdge]

class RedundantItem(BaseModel):
    type: str
    value: str
    locations: List[Dict[str, Any]]
    suggestion: Optional[str] = None

class OptimizationSuggestion(BaseModel):
    category: str
    issue: str
    severity: str
    suggestion: str
    affected_items: List[str]

class CSSAnalysisResult(BaseModel):
    url: str
    total_rules: int
    total_classes: int
    total_selectors: int
    css_sources: List[Dict[str, Any]]
    graph_data: CSSGraphData
    redundant_items: List[RedundantItem]
    optimization_suggestions: List[OptimizationSuggestion]
    statistics: Dict[str, Any]

class URLAnalysisRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL of the webpage to analyze")
    options: Optional[Dict[str, bool]] = Field(
        default={"include_inline": True, "include_external": True, "deep_analysis": True},
        description="Analysis options"
    )

class LLMConfig(BaseModel):
    base_url: str = Field(..., description="Base URL for OpenAI-compatible API")
    api_key: str = Field(..., description="API key for the LLM service")
    model_name: str = Field(..., description="Model name to use")
    enabled: bool = Field(default=False, description="Whether LLM integration is enabled")

class LLMTestResult(BaseModel):
    success: bool
    message: str
    model_info: Optional[Dict[str, Any]] = None

class ReportExportRequest(BaseModel):
    analysis_id: str
    format: str = Field(default="html", description="Export format: html, pdf, or json")
    include_visualization: bool = Field(default=True)

class CSSAnalysisResponse(BaseModel):
    analysis_id: str
    result: CSSAnalysisResult
