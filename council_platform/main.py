"""Council Platform — FastAPI application entry point."""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from council_platform.database import DB_PATH, init_db
from council_platform.orchestrator import classify_intent, event_bus, run_council_session
from council_platform.seed import seed_database

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Council Platform", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

from jinja2 import Environment, FileSystemLoader

_jinja_env = Environment(
    loader=FileSystemLoader(str(BASE_DIR / "templates")),
    auto_reload=True,
)
templates = Jinja2Templates(env=_jinja_env)

# Register filters
def _format_cost(cost):
    if cost == 0: return "mock"
    if cost < 0.01: return f"${cost:.4f}"
    return f"${cost:.3f}"

templates.env.filters["format_cost"] = _format_cost


@app.on_event("startup")
async def startup():
    await init_db()
    await seed_database()


# ── Helpers ────────────────────────────────────────────────────────────────

async def get_recent_sessions(limit: int = 10, council_type: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if council_type:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE council_type=? ORDER BY created_at DESC LIMIT ?",
                (council_type, limit)
            )
            return [dict(row) for row in await cursor.fetchall()]
        else:
            cursor = await db.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return [dict(row) for row in await cursor.fetchall()]


async def get_session(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_session_turns(session_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT dt.*, a.name as agent_name, a.icon as agent_icon, a.cognitive_function
               FROM deliberation_turns dt
               JOIN agents a ON dt.agent_id = a.id
               WHERE dt.session_id=?
               ORDER BY dt.phase, dt.turn_order, dt.started_at""",
            (session_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_session_synthesis(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM syntheses WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_template(template_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM council_templates WHERE id=?", (template_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_agents() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM agents ORDER BY cognitive_function, name")
        return [dict(row) for row in await cursor.fetchall()]


async def get_agents_for_template(template: dict) -> list[dict]:
    agent_ids = json.loads(template["agent_ids"])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        placeholders = ",".join("?" * len(agent_ids))
        cursor = await db.execute(
            f"SELECT * FROM agents WHERE id IN ({placeholders})", agent_ids
        )
        agents = [dict(row) for row in await cursor.fetchall()]
    agent_map = {a["id"]: a for a in agents}
    return [agent_map[aid] for aid in agent_ids if aid in agent_map]


async def get_all_templates() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM council_templates ORDER BY type, name")
        return [dict(row) for row in await cursor.fetchall()]


def council_type_meta(council_type: str) -> dict:
    """Return metadata for a council type."""
    meta = {
        "selves": {"icon": "🪞", "color": "#76d6d5", "label": "Council of Selves"},
        "idea": {"icon": "⚔️", "color": "#ffbf00", "label": "Idea Council"},
        "innovation": {"icon": "🔬", "color": "#dab9ff", "label": "Innovation Council"},
        "custom": {"icon": "🎛️", "color": "#879392", "label": "Custom Council"},
    }
    return meta.get(council_type, {"icon": "🏛️", "color": "#76d6d5", "label": "Council"})

# Register as Jinja globals (available in all templates)
templates.env.globals["council_type_meta"] = council_type_meta
templates.env.globals["classify_intent"] = classify_intent

def parse_tags(tags_str):
    if not tags_str:
        return []
    try:
        return json.loads(tags_str)
    except (json.JSONDecodeError, TypeError):
        return []

templates.env.globals["parse_tags"] = parse_tags

FUNCTION_LABELS = {
    "evaluative": {"label": "Evaluative", "description": "Converge toward truth", "icon": "🎯"},
    "generative": {"label": "Generative", "description": "Expand the possibility space", "icon": "✨"},
    "introspective": {"label": "Introspective", "description": "Inner parts dialogue", "icon": "🪞"},
    "relational": {"label": "Relational", "description": "Perspective-taking", "icon": "👥"},
    "integrative": {"label": "Integrative", "description": "Synthesise toward coherence", "icon": "🧵"},
    "meta": {"label": "Meta / Structural", "description": "Operate on the process itself", "icon": "⚙️"},
}
templates.env.globals["function_labels"] = FUNCTION_LABELS


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    recent = await get_recent_sessions(limit=8)
    template = templates.get_template("home.html")
    return template.render({
        "request": request, "recent_sessions": recent, "canonical_templates": [],
        "page": "home",
    })


@app.get("/sessions", response_class=HTMLResponse)
async def sessions_list(request: Request, council_type: Optional[str] = None):
    sessions = await get_recent_sessions(limit=50, council_type=council_type)
    return templates.TemplateResponse("sessions_list.html", {
        "request": request, "sessions": sessions, "filter_type": council_type,
        "page": "sessions",
    })


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_view(request: Request, session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Not found")
    
    turns = await get_session_turns(session_id)
    synthesis = await get_session_synthesis(session_id)
    
    phases = {}
    for turn in turns:
        phase = turn.get("phase", 1)
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(turn)
    
    total_cost = sum(t.get("cost_usd", 0) or 0 for t in turns)
    if synthesis:
        total_cost += synthesis.get("cost_usd", 0) or 0
    
    return templates.TemplateResponse("session.html", {
        "request": request, "session": session, "turns": turns, "phases": phases,
        "synthesis": synthesis, "total_cost": total_cost,
        "meta": council_type_meta(session["council_type"]), "page": "session",
    })


@app.post("/deliberate")
async def start_deliberation(
    input_text: str = Form(...),
    council_type: str = Form(default="idea"),
    template_id: str = Form(default=""),
    title: str = Form(default=""),
):
    if not template_id:
        mapping = {"selves": "council-of-selves", "idea": "idea-council", "innovation": "innovation-council"}
        template_id = mapping.get(council_type, "idea-council")
    
    template = await get_template(template_id)
    if not template:
        raise HTTPException(status_code=400, detail=f"Template {template_id} not found")
    
    agents = await get_agents_for_template(template)
    if not agents:
        raise HTTPException(status_code=400, detail="No agents found")
    
    if not title:
        words = input_text.split()
        title = " ".join(words[:8]) + ("..." if len(words) > 8 else "")
    
    session_id = str(uuid.uuid4())
    
    actual_council_type = council_type
    if template["type"] == "canonical":
        name_map = {
            "council-of-selves": "selves",
            "idea-council": "idea",
            "innovation-council": "innovation",
        }
        actual_council_type = name_map.get(template_id, council_type)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO sessions (id, council_template_id, council_type, title, input_text, status)
               VALUES (?, ?, ?, ?, ?, 'active')""",
            (session_id, template_id, actual_council_type, title, input_text)
        )
        for agent in agents:
            await db.execute(
                "INSERT INTO session_agents (id, session_id, agent_id) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), session_id, agent["id"])
            )
        await db.commit()
    
    phase_config = None
    if template.get("phase_config"):
        phase_config = json.loads(template["phase_config"])
    
    asyncio.create_task(run_council_session(
        session_id=session_id, agents=agents, input_text=input_text,
        council_type=actual_council_type, mode=template["mode"], phase_config=phase_config,
    ))
    
    return RedirectResponse(url=f"/sessions/{session_id}", status_code=303)


@app.get("/stream/{session_id}")
async def stream_session(session_id: str):
    async def event_generator():
        try:
            async for event in event_bus.subscribe(session_id):
                event_type = event.get("type", "message")
                event_data = {k: v for k, v in event.items() if k != "type"}
                yield {"event": event_type, "data": json.dumps(event_data)}
                if event_type == "session_completed":
                    break
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
        finally:
            event_bus.cleanup(session_id)
    return EventSourceResponse(event_generator())


@app.get("/agents", response_class=HTMLResponse)
async def agents_browser(request: Request):
    agents = await get_all_agents()
    groups = {}
    for agent in agents:
        fn = agent.get("cognitive_function", "other")
        if fn not in groups:
            groups[fn] = []
        groups[fn].append(agent)
    function_labels = {
        "evaluative": {"label": "Evaluative", "description": "Converge toward truth", "icon": "🎯"},
        "generative": {"label": "Generative", "description": "Expand the possibility space", "icon": "✨"},
        "introspective": {"label": "Introspective", "description": "Inner parts dialogue", "icon": "🪞"},
        "relational": {"label": "Relational", "description": "Perspective-taking", "icon": "👥"},
        "integrative": {"label": "Integrative", "description": "Synthesise toward coherence", "icon": "🧵"},
        "meta": {"label": "Meta / Structural", "description": "Operate on the process itself", "icon": "⚙️"},
    }
    return templates.TemplateResponse("agents.html", {
        "request": request, "agents": agents, "groups": groups,
        "page": "agents",
    })


@app.get("/selves", response_class=HTMLResponse)
async def selves_landing(request: Request):
    sessions = await get_recent_sessions(limit=5, council_type="selves")
    return templates.TemplateResponse("home.html", {
        "request": request, "recent_sessions": sessions, "page": "home",
        "forced_council_type": "selves", "forced_template_id": "council-of-selves",
        "council_label": "Council of Selves",
        "council_prompt": "What decision or dilemma is weighing on you?",
        "council_type_meta": council_type_meta,
    })


@app.get("/ideas", response_class=HTMLResponse)
async def ideas_landing(request: Request):
    sessions = await get_recent_sessions(limit=5, council_type="idea")
    return templates.TemplateResponse("home.html", {
        "request": request, "recent_sessions": sessions, "page": "home",
        "forced_council_type": "idea", "forced_template_id": "idea-council",
        "council_label": "Idea Council",
        "council_prompt": "What idea do you want stress-tested?",
        "council_type_meta": council_type_meta,
    })


@app.get("/lab", response_class=HTMLResponse)
async def lab_landing(request: Request):
    sessions = await get_recent_sessions(limit=5, council_type="innovation")
    return templates.TemplateResponse("home.html", {
        "request": request, "recent_sessions": sessions, "page": "home",
        "forced_council_type": "innovation", "forced_template_id": "innovation-council",
        "council_label": "Innovation Council",
        "council_prompt": "What theme or territory do you want to explore?",
        "council_type_meta": council_type_meta,
    })


@app.get("/builder", response_class=HTMLResponse)
async def builder(request: Request):
    agents = await get_all_agents()
    all_templates = await get_all_templates()
    return templates.TemplateResponse("builder.html", {
        "request": request, "agents": agents, "saved_templates": all_templates, "page": "builder",
    })


@app.post("/builder/save")
async def save_custom_council(
    name: str = Form(...),
    agent_ids: str = Form(...),
    mode: str = Form(default="parallel"),
    description: str = Form(default=""),
):
    agent_id_list = json.loads(agent_ids)
    template_id = f"custom-{uuid.uuid4().hex[:8]}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO council_templates 
               (id, name, type, agent_ids, mode, description, icon, accent_color)
               VALUES (?, ?, 'custom', ?, ?, ?, '🎛️', '#879392')""",
            (template_id, name, json.dumps(agent_id_list), mode, description)
        )
        await db.commit()
    return {"success": True, "template_id": template_id}


@app.get("/classify-intent")
async def classify_intent_api(q: str):
    return {"intent": classify_intent(q), "query": q}


@app.get("/chain/{session_id}", response_class=HTMLResponse)
async def chain_session(request: Request, session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404)
    synthesis = await get_session_synthesis(session_id)
    if not synthesis:
        raise HTTPException(status_code=400, detail="No synthesis to chain from")
    chain_map = {"innovation": "idea", "idea": "selves", "selves": "innovation"}
    next_type = chain_map.get(session["council_type"], "idea")
    template_map = {"selves": "council-of-selves", "idea": "idea-council", "innovation": "innovation-council"}
    return templates.TemplateResponse("home.html", {
        "request": request, "recent_sessions": [], "page": "home",
        "chain_from": session, "chain_input": synthesis["content"][:2000],
        "suggested_council_type": next_type,
        "suggested_template_id": template_map.get(next_type, "idea-council"),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8510)
