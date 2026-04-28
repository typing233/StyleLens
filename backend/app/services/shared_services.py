from typing import Dict, Optional
from app.services.llm_service import LLMService
from app.services.css_extractor import CSSExtractor
from app.services.css_analyzer import CSSAnalyzer
from app.services.report_generator import ReportGenerator
from app.models.schemas import CSSAnalysisResult

_llm_service: Optional[LLMService] = None
_css_extractor: Optional[CSSExtractor] = None
_css_analyzer: Optional[CSSAnalyzer] = None
_report_generator: Optional[ReportGenerator] = None
_analysis_cache: Dict[str, CSSAnalysisResult] = {}
_current_analysis_id: Optional[str] = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

def get_css_extractor() -> CSSExtractor:
    global _css_extractor
    if _css_extractor is None:
        _css_extractor = CSSExtractor()
    return _css_extractor

def get_css_analyzer() -> CSSAnalyzer:
    global _css_analyzer
    if _css_analyzer is None:
        _css_analyzer = CSSAnalyzer()
    return _css_analyzer

def get_report_generator() -> ReportGenerator:
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator

def get_analysis_cache() -> Dict[str, CSSAnalysisResult]:
    global _analysis_cache
    return _analysis_cache

def cache_analysis(analysis_id: str, result: CSSAnalysisResult) -> None:
    global _analysis_cache, _current_analysis_id
    _analysis_cache[analysis_id] = result
    _current_analysis_id = analysis_id

def get_analysis(analysis_id: str) -> Optional[CSSAnalysisResult]:
    global _analysis_cache
    return _analysis_cache.get(analysis_id)

def get_current_analysis() -> Optional[CSSAnalysisResult]:
    global _analysis_cache, _current_analysis_id
    if _current_analysis_id and _current_analysis_id in _analysis_cache:
        return _analysis_cache[_current_analysis_id]
    return None

def get_current_analysis_id() -> Optional[str]:
    global _current_analysis_id
    return _current_analysis_id

def delete_analysis(analysis_id: str) -> bool:
    global _analysis_cache, _current_analysis_id
    if analysis_id in _analysis_cache:
        del _analysis_cache[analysis_id]
        if _current_analysis_id == analysis_id:
            _current_analysis_id = None
        return True
    return False

def clear_all_caches() -> None:
    global _analysis_cache, _current_analysis_id
    _analysis_cache = {}
    _current_analysis_id = None
