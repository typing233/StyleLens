from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import uuid
from app.models.schemas import (
    URLAnalysisRequest, CSSAnalysisResult,
    ReportExportRequest
)
from app.services.css_extractor import CSSExtractor
from app.services.css_analyzer import CSSAnalyzer
from app.services.report_generator import ReportGenerator
from app.services.llm_service import LLMService

router = APIRouter()

css_extractor = CSSExtractor()
css_analyzer = CSSAnalyzer()
report_generator = ReportGenerator()
llm_service = LLMService()

analysis_cache: Dict[str, CSSAnalysisResult] = {}

def get_llm_service():
    return llm_service

@router.post("/analyze", response_model=CSSAnalysisResult)
async def analyze_url(request: URLAnalysisRequest):
    try:
        url = str(request.url)
        
        rules, css_sources = css_extractor.extract_from_url(url, request.options)
        
        if not rules:
            raise HTTPException(
                status_code=404,
                detail="No CSS rules found for the provided URL"
            )
        
        graph_data, redundant_items, optimization_suggestions, statistics = css_analyzer.analyze(rules)
        
        result = CSSAnalysisResult(
            url=url,
            total_rules=len(rules),
            total_classes=len(graph_data.nodes),
            total_selectors=len(set(r.selector for r in rules)),
            css_sources=css_sources,
            graph_data=graph_data,
            redundant_items=redundant_items,
            optimization_suggestions=optimization_suggestions,
            statistics=statistics
        )
        
        analysis_id = str(uuid.uuid4())
        analysis_cache[analysis_id] = result
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing URL: {str(e)}"
        )

@router.post("/report/export")
async def export_report(request: ReportExportRequest):
    try:
        analysis_result = None
        
        if request.analysis_id in analysis_cache:
            analysis_result = analysis_cache[request.analysis_id]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {request.analysis_id} not found"
            )
        
        report = report_generator.generate_report(analysis_result, request.format)
        
        return {
            "success": True,
            "format": request.format,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    if analysis_id not in analysis_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    
    return analysis_cache[analysis_id]

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    if analysis_id in analysis_cache:
        del analysis_cache[analysis_id]
        return {"success": True, "message": "Analysis deleted"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )

@router.post("/llm/analyze")
async def llm_analyze(analysis_id: str, custom_prompt: str = None, llm_svc: LLMService = Depends(get_llm_service)):
    try:
        if analysis_id not in analysis_cache:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        if not llm_svc.is_configured():
            raise HTTPException(
                status_code=400,
                detail="LLM service is not configured. Please configure LLM settings first."
            )
        
        analysis_result = analysis_cache[analysis_id]
        
        analysis_summary = {
            "url": analysis_result.url,
            "total_rules": analysis_result.total_rules,
            "total_classes": analysis_result.total_classes,
            "statistics": analysis_result.statistics,
            "redundant_items": [item.model_dump() for item in analysis_result.redundant_items],
            "optimization_suggestions": [item.model_dump() for item in analysis_result.optimization_suggestions]
        }
        
        llm_insights = llm_svc.analyze_css_with_llm(analysis_summary, custom_prompt)
        
        if llm_insights is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to get LLM analysis"
            )
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "llm_insights": llm_insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in LLM analysis: {str(e)}"
        )

@router.post("/llm/refactor")
async def llm_refactor(analysis_id: str, llm_svc: LLMService = Depends(get_llm_service)):
    try:
        if analysis_id not in analysis_cache:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        if not llm_svc.is_configured():
            raise HTTPException(
                status_code=400,
                detail="LLM service is not configured. Please configure LLM settings first."
            )
        
        analysis_result = analysis_cache[analysis_id]
        
        rules_summary = []
        for node in analysis_result.graph_data.nodes[:30]:
            for rule in node.rules[:3]:
                rules_summary.append({
                    "selector": rule.selector,
                    "declarations": rule.declarations
                })
        
        suggestions = [s.model_dump() for s in analysis_result.optimization_suggestions]
        
        refactored_css = llm_svc.generate_refactored_css(rules_summary, suggestions)
        
        if refactored_css is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate refactored CSS"
            )
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "refactored_css": refactored_css
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating refactored CSS: {str(e)}"
        )
