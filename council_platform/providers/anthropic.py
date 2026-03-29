"""Anthropic (Claude) provider for agent execution."""

import os
import time
import json
from dataclasses import dataclass
from typing import AsyncGenerator

PRICING = {
    "claude-opus-4-5": {"input": 15.0 / 1_000_000, "output": 75.0 / 1_000_000},
    "claude-sonnet-4-5": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-haiku-3-5": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
    "claude-opus-4-6": {"input": 15.0 / 1_000_000, "output": 75.0 / 1_000_000},
    "claude-sonnet-4-6": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
}

DEFAULT_MODEL = "claude-sonnet-4-5"


@dataclass
class AgentResult:
    agent_id: str
    content: str
    confidence: float | None
    model_used: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    duration_ms: int


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    rates = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return (tokens_in * rates["input"]) + (tokens_out * rates["output"])


async def generate_with_anthropic(
    agent_id: str,
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    on_token: callable = None,
) -> AgentResult:
    """Generate a response using Anthropic API with optional streaming."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        # Mock response for testing without API key
        return _mock_response(agent_id, model)
    
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        start_time = time.time()
        content_parts = []
        tokens_in = 0
        tokens_out = 0
        
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                content_parts.append(text)
                if on_token:
                    await on_token(text)
            
            final = await stream.get_final_message()
            tokens_in = final.usage.input_tokens
            tokens_out = final.usage.output_tokens
        
        content = "".join(content_parts)
        duration_ms = int((time.time() - start_time) * 1000)
        cost_usd = calculate_cost(model, tokens_in, tokens_out)
        
        # Extract confidence if present in content
        confidence = _extract_confidence(content)
        
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
        return _error_response(agent_id, model, str(e))


def _extract_confidence(content: str) -> float | None:
    """Extract confidence score from agent output if present."""
    import re
    # Look for patterns like "CONFIDENCE: 0.75" or "confidence_score: 0.8"
    patterns = [
        r'CONFIDENCE[:\s]+([0-9.]+)',
        r'confidence[_\s]score[:\s]+([0-9.]+)',
        r'\[CONFIDENCE:?\s*([0-9.]+)\]',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 0 <= val <= 1:
                    return val
            except ValueError:
                pass
    return None


def _mock_response(agent_id: str, model: str) -> AgentResult:
    """Return a mock response when no API key is configured."""
    content = f"""## Analysis from {agent_id.replace('-', ' ').title()}

This is a placeholder response. To see real AI-generated content, configure your `ANTHROPIC_API_KEY` environment variable.

The deliberation would proceed here with genuine analysis of your question. Each agent would bring their unique cognitive lens to examine the problem from different angles.

**Key observations:**
- The question raises important considerations worth exploring
- Multiple perspectives would reveal tensions and alignments
- Synthesis would emerge from the structured deliberation

CONFIDENCE: 0.75"""
    
    return AgentResult(
        agent_id=agent_id,
        content=content,
        confidence=0.75,
        model_used=f"{model} (mock)",
        tokens_in=0,
        tokens_out=0,
        cost_usd=0.0,
        duration_ms=500,
    )


def _error_response(agent_id: str, model: str, error: str) -> AgentResult:
    """Return an error response."""
    return AgentResult(
        agent_id=agent_id,
        content=f"**Error:** {error}\n\nThis agent encountered an issue generating a response.",
        confidence=None,
        model_used=model,
        tokens_in=0,
        tokens_out=0,
        cost_usd=0.0,
        duration_ms=0,
    )
