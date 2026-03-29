"""Google (Gemini) provider for agent execution."""

import os
import time
from dataclasses import dataclass

PRICING = {
    "gemini-1.5-pro": {"input": 1.25 / 1_000_000, "output": 5.0 / 1_000_000},
    "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
    "gemini-2.0-flash": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
}

DEFAULT_MODEL = "gemini-1.5-pro"


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    rates = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return (tokens_in * rates["input"]) + (tokens_out * rates["output"])


async def generate_with_google(
    agent_id: str,
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
    max_tokens: int = 1500,
    on_token: callable = None,
) -> "AgentResult":
    """Generate a response using Google Gemini API."""
    from council_platform.providers.anthropic import AgentResult, _extract_confidence
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        return _mock_response(agent_id, model)
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        start_time = time.time()
        
        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        
        response = gen_model.generate_content(user_message)
        content = response.text
        
        # Gemini token counting
        tokens_in = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        tokens_out = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        
        duration_ms = int((time.time() - start_time) * 1000)
        cost_usd = calculate_cost(model, tokens_in, tokens_out)
        confidence = _extract_confidence(content)
        
        if on_token:
            # For Gemini we don't have token streaming, emit whole content
            await on_token(content)
        
        return AgentResult(
            agent_id=agent_id,
            content=content,
            confidence=confidence,
            model_used=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
        )
    
    except Exception as e:
        from council_platform.providers.anthropic import _error_response
        return _error_response(agent_id, model, str(e))


def _mock_response(agent_id: str, model: str):
    """Return a mock Gemini response when no API key is configured."""
    from council_platform.providers.anthropic import AgentResult
    
    content = f"""## Gemini Analysis from {agent_id.replace('-', ' ').title()}

This is a placeholder response from the Gemini provider. Configure `GOOGLE_API_KEY` to enable real responses.

The Innovation Council uses Gemini alongside Claude to achieve genuine cognitive diversity — different model architectures produce structurally different patterns of attention, association, and synthesis.

**Cross-domain observations:**
- Structural analogues from adjacent fields suggest new possibilities
- Weak signals in the data hint at emerging patterns
- The combination of perspectives creates emergent insights

CONFIDENCE: 0.78"""
    
    return AgentResult(
        agent_id=agent_id,
        content=content,
        confidence=0.78,
        model_used=f"{model} (mock)",
        tokens_in=0,
        tokens_out=0,
        cost_usd=0.0,
        duration_ms=400,
    )
