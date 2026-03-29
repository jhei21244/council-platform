"""Council Orchestrator — manages parallel, sequential, and phased agent execution."""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import AsyncGenerator, Callable

import aiosqlite

from council_platform.database import DB_PATH
from council_platform.providers.anthropic import (
    generate_with_anthropic,
    AgentResult,
    DEFAULT_MODEL as CLAUDE_DEFAULT,
)
from council_platform.providers.google import (
    generate_with_google,
    DEFAULT_MODEL as GEMINI_DEFAULT,
)

# Cost pricing (merged here for convenience)
CLAUDE_PRICING = {
    "claude-sonnet-4-5": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-opus-4-5": {"input": 15.0 / 1_000_000, "output": 75.0 / 1_000_000},
}


class SessionEventBus:
    """Simple in-memory event bus for SSE streaming."""
    
    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
    
    def get_or_create(self, session_id: str) -> asyncio.Queue:
        if session_id not in self._queues:
            self._queues[session_id] = asyncio.Queue()
        return self._queues[session_id]
    
    async def publish(self, session_id: str, event: dict):
        queue = self.get_or_create(session_id)
        await queue.put(event)
    
    async def subscribe(self, session_id: str) -> AsyncGenerator:
        queue = self.get_or_create(session_id)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=120)
                yield event
                if event.get("type") == "session_completed":
                    break
            except asyncio.TimeoutError:
                break
    
    def cleanup(self, session_id: str):
        self._queues.pop(session_id, None)


# Global event bus
event_bus = SessionEventBus()


def classify_intent(text: str) -> str:
    """Keyword-based intent classification for the smart input bar."""
    text_lower = text.lower()
    
    selves_patterns = [
        "should i", "i'm torn", "i feel", "part of me", "i want to",
        "don't know if i", "can't decide", "afraid", "worried about myself",
        "what do i really", "inner", "authentic", "my gut", "conflicted",
        "scared to", "holding back", "i keep", "pattern i notice",
    ]
    
    ideas_patterns = [
        "i have an idea", "what if we", "my idea", "i'm building", "startup",
        "product idea", "business idea", "i want to launch", "i'm working on",
        "proposal", "concept i have", "pitch", "evaluate this", "feedback on",
        "stress test", "critique my",
    ]
    
    innovation_patterns = [
        "what opportunities", "explore", "what's possible", "emerging", 
        "future of", "space of", "landscape of", "what could", "imagine",
        "possibilities in", "opportunities in", "what if the world", "trends",
        "innovate", "disrupt", "whitespace", "underexplored",
    ]
    
    for p in selves_patterns:
        if p in text_lower:
            return "selves"
    
    for p in ideas_patterns:
        if p in text_lower:
            return "idea"
    
    for p in innovation_patterns:
        if p in text_lower:
            return "innovation"
    
    return "unknown"


def build_user_message(input_text: str, agent: dict, prior_results: list[AgentResult] | None = None, phase: int = 1) -> str:
    """Build the user message for an agent, optionally including prior results for cross-pollination."""
    base_message = f"""## The Question / Theme / Proposal

{input_text}

---

Please provide your analysis in your distinctive voice. Be specific, not generic. Format your response with clear headings in markdown.

Remember to end your response with: CONFIDENCE: [0.0-1.0]"""
    
    if prior_results and phase > 1:
        prior_content = "\n\n".join([
            f"### {r.agent_id.replace('-', ' ').title()}'s Phase 1 Analysis\n\n{r.content}"
            for r in prior_results
        ])
        base_message = f"""## The Question / Theme / Proposal

{input_text}

---

## Phase 1 Analyses From Other Agents

{prior_content}

---

## Your Task for Phase 2

You've seen what your colleagues produced in Phase 1. Now respond with cross-pollination in mind: 
- What does their work open up that you hadn't considered?
- Where do you see a productive collision with your own perspective?
- What new insight emerges from the combination?

Build on the collective intelligence above, don't just repeat your own Phase 1 analysis.

Remember to end your response with: CONFIDENCE: [0.0-1.0]"""
    
    return base_message


async def run_agent(
    session_id: str,
    agent: dict,
    input_text: str,
    phase: int = 1,
    prior_results: list[AgentResult] | None = None,
    model_override: str | None = None,
) -> AgentResult:
    """Run a single agent and publish events to the bus."""
    
    agent_id = agent["id"]
    default_model = agent.get("default_model", "claude")
    
    # Determine model to use
    if model_override:
        model = model_override
        provider = "google" if "gemini" in model else "anthropic"
    elif default_model == "gemini":
        model = GEMINI_DEFAULT
        provider = "google"
    else:
        model = CLAUDE_DEFAULT
        provider = "anthropic"
    
    # Publish agent_started event
    await event_bus.publish(session_id, {
        "type": "agent_started",
        "agent_id": agent_id,
        "phase": phase,
        "model": model,
        "provider": provider,
    })
    
    user_message = build_user_message(input_text, agent, prior_results, phase)
    
    tokens_buffer = []
    
    async def on_token(token: str):
        tokens_buffer.append(token)
        await event_bus.publish(session_id, {
            "type": "agent_token",
            "agent_id": agent_id,
            "token": token,
            "phase": phase,
        })
    
    # Execute
    if provider == "google":
        result = await generate_with_google(
            agent_id=agent_id,
            system_prompt=agent["system_prompt"],
            user_message=user_message,
            model=model,
            on_token=on_token,
        )
    else:
        result = await generate_with_anthropic(
            agent_id=agent_id,
            system_prompt=agent["system_prompt"],
            user_message=user_message,
            model=model,
            on_token=on_token,
        )
    
    # Persist to DB
    async with aiosqlite.connect(DB_PATH) as db:
        turn_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO deliberation_turns 
               (id, session_id, agent_id, phase, content, confidence, model_used, 
                tokens_in, tokens_out, cost_usd, started_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                turn_id, session_id, agent_id, phase,
                result.content, result.confidence, result.model_used,
                result.tokens_in, result.tokens_out, result.cost_usd,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            )
        )
        await db.commit()
    
    # Publish agent_completed event
    await event_bus.publish(session_id, {
        "type": "agent_completed",
        "agent_id": agent_id,
        "phase": phase,
        "content": result.content,
        "confidence": result.confidence,
        "cost_usd": result.cost_usd,
        "model_used": result.model_used,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
    })
    
    return result


async def run_synthesis(
    session_id: str,
    all_results: list[AgentResult],
    input_text: str,
    council_type: str,
    model: str = CLAUDE_DEFAULT,
) -> str:
    """Run the synthesis agent that reads all prior outputs."""
    
    await event_bus.publish(session_id, {"type": "synthesis_started"})
    
    agent_summaries = "\n\n".join([
        f"### {r.agent_id.replace('-', ' ').title()}\n\n{r.content}"
        for r in all_results
    ])
    
    synthesis_prompts = {
        "selves": """You are the Council Synthesiser for the Council of Selves. Your job is to produce the Mirror View — a reflective synthesis of what the inner parts have revealed.

Your Mirror View should:
1. Name the central tension between the parts (where they most clearly disagree)
2. Identify where the parts are aligned (the surprising agreements)
3. Surface what The Night Worker and less-vocal parts contributed that's easy to miss
4. Name the blind spot — what none of the parts seem to see
5. Offer a reflection from the observing Self (the awareness above the parts): what does all of this point toward?

Format as a reflective document with clear sections. Tone: gentle, clear, non-prescriptive. Do not tell the person what to do. Help them see what's already there.""",

        "idea": """You are the Council Synthesiser for the Idea Council. Your job is to produce a convergent synthesis from the five agents' evaluations.

Your synthesis should include:
1. **The Signal** — the strongest, most agreed-upon insight across the evaluations
2. **The Key Tension** — the most significant disagreement, stated fairly
3. **Convergences** — where agents landed in similar places (even if for different reasons)
4. **Blind Spots** — what the council might have missed collectively
5. **Three Questions to Sit With** — not verdicts, but questions that need honest answers before proceeding

Format as a structured synthesis document. Tone: rigorous but not harsh. The goal is clarity, not a verdict.""",

        "innovation": """You are the Council Synthesiser for the Innovation Council. Your job is to produce an Opportunity Map from the two-phase deliberation.

Your Opportunity Map should include:
1. **Opportunity 1** — the strongest opportunity identified (name, description, why it's real)
2. **Opportunity 2** — the second most compelling opportunity
3. **Opportunity 3** — the most provocative/speculative opportunity worth considering
4. **The Undercurrent** — the meta-pattern connecting all the individual opportunities
5. **The Discomfort** — the frame-challenging observation that most disrupts conventional thinking about this space

Format as a strategic synthesis document. Tone: generative and grounded.""",

        "custom": """You are the Council Synthesiser. Your job is to find the signal in the collective deliberation.

Your synthesis should:
1. **The Core Insight** — the single most important thing that emerged from the deliberation
2. **Agreements and Tensions** — where agents converged, where they diverged
3. **What's Been Revealed** — what wasn't visible before this deliberation
4. **Recommended Next Steps** — 2-3 concrete next actions based on the deliberation
5. **Questions Still Open** — what remains unresolved

Format clearly with headings. Be concrete, not vague.""",
    }
    
    synthesis_prompt = synthesis_prompts.get(council_type, synthesis_prompts["custom"])
    
    synthesis_message = f"""## Original Input

{input_text}

## Agent Deliberations

{agent_summaries}

---

Please produce your synthesis now."""
    
    tokens_buffer = []
    
    async def on_token(token: str):
        tokens_buffer.append(token)
        await event_bus.publish(session_id, {
            "type": "synthesis_token",
            "token": token,
        })
    
    result = await generate_with_anthropic(
        agent_id="synthesiser",
        system_prompt=synthesis_prompt,
        user_message=synthesis_message,
        model=model,
        temperature=0.5,
        max_tokens=2000,
        on_token=on_token,
    )
    
    # Persist synthesis
    total_cost = sum(r.cost_usd for r in all_results) + result.cost_usd
    
    async with aiosqlite.connect(DB_PATH) as db:
        synth_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO syntheses 
               (id, session_id, content, synthesis_type, model_used, tokens_in, tokens_out, cost_usd)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (synth_id, session_id, result.content, council_type, result.model_used,
             result.tokens_in, result.tokens_out, result.cost_usd)
        )
        
        # Mark session complete
        await db.execute(
            "UPDATE sessions SET status='completed', completed_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), session_id)
        )
        await db.commit()
    
    await event_bus.publish(session_id, {
        "type": "synthesis_completed",
        "content": result.content,
        "cost_usd": result.cost_usd,
        "total_cost": total_cost,
    })
    
    await event_bus.publish(session_id, {"type": "session_completed"})
    
    return result.content


async def run_council_session(
    session_id: str,
    agents: list[dict],
    input_text: str,
    council_type: str,
    mode: str,
    phase_config: dict | None = None,
):
    """Main orchestration function — runs a complete council session."""
    
    all_results = []
    
    try:
        if mode == "parallel":
            # All agents run in parallel
            tasks = [
                run_agent(session_id, agent, input_text, phase=1)
                for agent in agents
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results = [r for r in results if isinstance(r, AgentResult)]
            
            await event_bus.publish(session_id, {"type": "phase_completed", "phase": 1})
        
        elif mode == "sequential":
            # Agents run in sequence, each seeing prior outputs
            prior = []
            for i, agent in enumerate(agents):
                result = await run_agent(
                    session_id, agent, input_text,
                    phase=1, prior_results=prior
                )
                prior.append(result)
                all_results.append(result)
            
            await event_bus.publish(session_id, {"type": "phase_completed", "phase": 1})
        
        elif mode == "dialogic":
            # Similar to sequential but framed as inner dialogue
            prior = []
            for agent in agents:
                result = await run_agent(
                    session_id, agent, input_text,
                    phase=1, prior_results=prior
                )
                prior.append(result)
                all_results.append(result)
            
            await event_bus.publish(session_id, {"type": "phase_completed", "phase": 1})
        
        elif mode == "phased" and phase_config:
            phases = phase_config.get("phases", [])
            
            phase1_results = []
            for i, phase_def in enumerate(phases):
                phase_num = i + 1
                phase_agent_ids = phase_def.get("agents", [agent["id"] for agent in agents])
                phase_agents = [a for a in agents if a["id"] in phase_agent_ids]
                phase_mode = phase_def.get("mode", "parallel")
                
                if phase_mode == "parallel":
                    tasks = [
                        run_agent(session_id, agent, input_text, phase=phase_num)
                        for agent in phase_agents
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    phase_results = [r for r in results if isinstance(r, AgentResult)]
                else:
                    # Sequential with prior context from phase 1
                    phase_results = []
                    for agent in phase_agents:
                        result = await run_agent(
                            session_id, agent, input_text,
                            phase=phase_num, prior_results=phase1_results
                        )
                        phase_results.append(result)
                
                all_results.extend(phase_results)
                
                if i == 0:
                    phase1_results = phase_results
                
                await event_bus.publish(session_id, {
                    "type": "phase_completed",
                    "phase": phase_num,
                    "phase_name": phase_def.get("name", f"Phase {phase_num}"),
                })
        
        # Run synthesis
        await run_synthesis(session_id, all_results, input_text, council_type)
    
    except Exception as e:
        await event_bus.publish(session_id, {
            "type": "error",
            "message": str(e),
        })
        await event_bus.publish(session_id, {"type": "session_completed"})
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE sessions SET status='error' WHERE id=?",
                (session_id,)
            )
            await db.commit()
