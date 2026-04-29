from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
from app.models.schemas import (
    URLAnalysisRequest, CSSAnalysisResult, CSSAnalysisResponse,
    ReportExportRequest
)
from app.services.shared_services import (
    get_css_extractor,
    get_css_analyzer,
    get_report_generator,
    get_llm_service,
    cache_analysis,
    get_analysis,
    get_current_analysis,
    get_current_analysis_id,
    delete_analysis,
    get_analysis_cache
)

router = APIRouter()

@router.post("/analyze", response_model=CSSAnalysisResponse)
async def analyze_url(request: URLAnalysisRequest):
    try:
        url = str(request.url)
        
        css_extractor = get_css_extractor()
        css_analyzer_service = get_css_analyzer()
        
        rules, css_sources = css_extractor.extract_from_url(url, request.options)
        
        if not rules:
            raise HTTPException(
                status_code=404,
                detail="No CSS rules found for the provided URL"
            )
        
        graph_data, redundant_items, optimization_suggestions, statistics = css_analyzer_service.analyze(rules)
        
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
        cache_analysis(analysis_id, result)
        
        return CSSAnalysisResponse(
            analysis_id=analysis_id,
            result=result
        )
        
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
        analysis_result = get_analysis(request.analysis_id)
        
        if analysis_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {request.analysis_id} not found"
            )
        
        report_generator = get_report_generator()
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

@router.post("/report/export-current")
async def export_current_report(format: str = "html", include_visualization: bool = True):
    try:
        analysis_result = get_current_analysis()
        
        if analysis_result is None:
            raise HTTPException(
                status_code=404,
                detail="No current analysis available. Please analyze a URL first."
            )
        
        analysis_id = get_current_analysis_id()
        
        report_generator = get_report_generator()
        report = report_generator.generate_report(analysis_result, format)
        
        return {
            "success": True,
            "format": format,
            "analysis_id": analysis_id,
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
async def get_analysis_by_id(analysis_id: str):
    analysis_result = get_analysis(analysis_id)
    
    if analysis_result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    
    return {
        "analysis_id": analysis_id,
        "result": analysis_result
    }

@router.get("/analysis/current")
async def get_current_analysis_endpoint():
    analysis_result = get_current_analysis()
    analysis_id = get_current_analysis_id()
    
    if analysis_result is None:
        raise HTTPException(
            status_code=404,
            detail="No current analysis available. Please analyze a URL first."
        )
    
    return {
        "analysis_id": analysis_id,
        "result": analysis_result
    }

@router.delete("/analysis/{analysis_id}")
async def delete_analysis_by_id(analysis_id: str):
    if delete_analysis(analysis_id):
        return {"success": True, "message": "Analysis deleted"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with ID {analysis_id} not found"
        )

@router.post("/llm/analyze")
async def llm_analyze(analysis_id: str = None, custom_prompt: str = None):
    try:
        llm_svc = get_llm_service()
        
        if not llm_svc.is_configured():
            raise HTTPException(
                status_code=400,
                detail="LLM service is not configured. Please configure LLM settings first."
            )
        
        if analysis_id:
            analysis_result = get_analysis(analysis_id)
        else:
            analysis_result = get_current_analysis()
            analysis_id = get_current_analysis_id()
        
        if analysis_result is None:
            raise HTTPException(
                status_code=404,
                detail="No analysis data available. Please provide an analysis_id or analyze a URL first."
            )
        
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
async def llm_refactor(analysis_id: str = None):
    try:
        llm_svc = get_llm_service()
        
        if not llm_svc.is_configured():
            raise HTTPException(
                status_code=400,
                detail="LLM service is not configured. Please configure LLM settings first."
            )
        
        if analysis_id:
            analysis_result = get_analysis(analysis_id)
        else:
            analysis_result = get_current_analysis()
            analysis_id = get_current_analysis_id()
        
        if analysis_result is None:
            raise HTTPException(
                status_code=404,
                detail="No analysis data available. Please provide an analysis_id or analyze a URL first."
            )
        
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

@router.get("/status")
async def get_status():
    llm_svc = get_llm_service()
    current_analysis_id = get_current_analysis_id()
    cache_size = len(get_analysis_cache())
    
    return {
        "llm_configured": llm_svc.is_configured(),
        "has_current_analysis": current_analysis_id is not None,
        "current_analysis_id": current_analysis_id,
        "cached_analyses_count": cache_size
    }
