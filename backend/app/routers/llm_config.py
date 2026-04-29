from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import LLMConfig, LLMTestResult
from app.services.llm_service import LLMService

router = APIRouter()

_llm_service: LLMService = None

def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

@router.post("/llm/configure")
async def configure_llm(config: LLMConfig, llm_svc: LLMService = Depends(get_llm_service)):
    try:
        llm_svc.configure(config)
        
        return {
            "success": True,
            "message": "LLM configuration updated successfully",
            "config": {
                "base_url": config.base_url,
                "model_name": config.model_name,
                "enabled": config.enabled
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring LLM: {str(e)}"
        )

@router.post("/llm/test", response_model=LLMTestResult)
async def test_llm_connection(config: LLMConfig, llm_svc: LLMService = Depends(get_llm_service)):
    try:
        result = llm_svc.test_connection(config)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing LLM connection: {str(e)}"
        )

@router.get("/llm/config")
async def get_llm_config(llm_svc: LLMService = Depends(get_llm_service)):
    config = llm_svc.get_current_config()
    
    if config is None:
        return {
            "configured": False,
            "message": "LLM is not configured"
        }
    
    return {
        "configured": True,
        "enabled": config.enabled,
        "base_url": config.base_url,
        "model_name": config.model_name
    }

@router.get("/llm/status")
async def get_llm_status(llm_svc: LLMService = Depends(get_llm_service)):
    return {
        "configured": llm_svc.is_configured(),
        "message": "LLM service is ready" if llm_svc.is_configured() else "LLM service is not configured"
    }

@router.delete("/llm/config")
async def clear_llm_config(llm_svc: LLMService = Depends(get_llm_service)):
    empty_config = LLMConfig(
        base_url="",
        api_key="",
        model_name="",
        enabled=False
    )
    llm_svc.configure(empty_config)
    
    return {
        "success": True,
        "message": "LLM configuration cleared"
    }
