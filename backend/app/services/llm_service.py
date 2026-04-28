from typing import Optional, Dict, Any, List
from openai import OpenAI
from app.models.schemas import LLMConfig, LLMTestResult

class LLMService:
    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._config: Optional[LLMConfig] = None

    def configure(self, config: LLMConfig) -> None:
        self._config = config
        if config.enabled and config.api_key and config.base_url:
            self._client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
        else:
            self._client = None

    def test_connection(self, config: LLMConfig) -> LLMTestResult:
        try:
            if not config.enabled:
                return LLMTestResult(
                    success=False,
                    message="LLM integration is disabled"
                )
            
            if not config.api_key:
                return LLMTestResult(
                    success=False,
                    message="API key is required"
                )
            
            if not config.base_url:
                return LLMTestResult(
                    success=False,
                    message="Base URL is required"
                )
            
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            
            response = client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": "Hello, please respond with 'OK' if you receive this message."}],
                max_tokens=10
            )
            
            model_info = {
                "model": config.model_name,
                "base_url": config.base_url,
                "response": response.choices[0].message.content if response.choices else None
            }
            
            return LLMTestResult(
                success=True,
                message=f"Successfully connected to {config.model_name}",
                model_info=model_info
            )
            
        except Exception as e:
            return LLMTestResult(
                success=False,
                message=f"Connection failed: {str(e)}"
            )

    def get_current_config(self) -> Optional[LLMConfig]:
        return self._config

    def is_configured(self) -> bool:
        return self._client is not None and self._config is not None and self._config.enabled

    def analyze_css_with_llm(self, css_analysis: Dict[str, Any], prompt: str = None) -> Optional[str]:
        if not self.is_configured():
            return None
        
        try:
            default_prompt = f"""
You are a CSS expert. Please analyze the following CSS analysis data and provide additional insights and optimization suggestions:

{css_analysis}

Please provide:
1. Additional architectural insights
2. Specific refactoring recommendations
3. Performance optimization tips
4. Best practice violations
"""
            
            final_prompt = prompt or default_prompt
            
            response = self._client.chat.completions.create(
                model=self._config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior CSS architect and performance optimization expert. Provide detailed, actionable insights about CSS code quality, architecture, and optimization opportunities."
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content if response.choices else None
            
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return None

    def generate_refactored_css(self, original_rules: List[Dict], suggestions: List[Dict]) -> Optional[str]:
        if not self.is_configured():
            return None
        
        try:
            prompt = f"""
Based on the following CSS rules and optimization suggestions, please generate a refactored version of the CSS:

Original Rules Summary:
{original_rules[:20]}

Optimization Suggestions:
{suggestions}

Please provide:
1. Refactored CSS with CSS variables for colors
2. Optimized selectors with reduced nesting
3. Consolidated duplicate styles
4. Proper comments explaining changes

Only output the CSS code without any additional text.
"""
            
            response = self._client.chat.completions.create(
                model=self._config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CSS refactoring expert. Generate clean, optimized CSS code based on the provided analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            return response.choices[0].message.content if response.choices else None
            
        except Exception as e:
            print(f"Error generating refactored CSS: {e}")
            return None
