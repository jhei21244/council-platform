# Council Platform

A FastAPI + Jinja2 + SQLite web application for multi-agent deliberation. Three canonical councils (Selves, Ideas, Innovation) plus custom composition and chaining.

## Setup

1. **Activate venv:**
   ```bash
   source /home/openclaw/.openclaw/workspace/tab_venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set API keys (optional):**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   export GOOGLE_API_KEY=AIza...
   ```

   If not set, the app will use mock responses for testing.

4. **Start the server:**
   ```bash
   python -m council_platform.main
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn council_platform.main:app --host 0.0.0.0 --port 8510 --reload
   ```

5. **Open browser:**
   Visit http://localhost:8510

## Features

### Phase 1: Foundation
- ✅ Platform homepage with smart input bar
- ✅ Council of Selves (6 inner parts, dialogic mode)
- ✅ Database with all 27 agent archetypes
- ✅ Session management and history
- ✅ Dark theme design (teal/amber/violet accents)

### Phase 2: Idea Council
- ✅ 5 evaluative agents (Prosecutor, Pivot Artist, Operator, Customer Voice, Contrarian)
- ✅ Parallel execution + synthesis
- ✅ Confidence bars and cost tracking

### Phase 3: Innovation Council
- ✅ 5 generative agents (Archaeologist, Void Reader, Collision Artist, Anthropologist, Signal Hunter)
- ✅ Two-phase execution (diverge → collide)
- ✅ Multi-model support (Claude + Gemini)
- ✅ Opportunity Map synthesis

### Phase 4+: Additional Features
- ✅ Strategy, Debug, Due Diligence, Ethics, Integration councils
- ✅ Custom council builder
- ✅ Session chaining
- ✅ Agent pool browser

## Architecture

```
council-platform/
├── council_platform/
│   ├── main.py              # FastAPI app, routes
│   ├── database.py          # SQLite setup
│   ├── seed.py              # 27 agents + 8 templates
│   ├── orchestrator.py      # Parallel/sequential/phased execution
│   ├── providers/
│   │   ├── anthropic.py     # Claude integration
│   │   └── google.py        # Gemini integration
│   ├── templates/           # Jinja2 HTML
│   └── static/              # CSS + JS
├── requirements.txt
└── README.md
```

## Database Schema

- **agents** — 27 archetypes with system prompts
- **council_templates** — 3 canonical + 5 specialized + user custom
- **sessions** — deliberation records, chainable
- **session_agents** — agent roster per session
- **deliberation_turns** — agent outputs with tokens/cost
- **syntheses** — convergent synthesis output

## SSE Streaming

Real-time agent results via `/stream/{session_id}`:
- `agent_started` — agent begins
- `agent_token` — incremental token (streaming)
- `agent_completed` — agent finished with full content
- `phase_completed` — phase boundary
- `synthesis_started/completed` — synthesis generation
- `session_completed` — end

## Design

- **Dark theme:** #101414 bg, #76d6d5 teal primary, #ffbf00 amber, #dab9ff violet
- **Fonts:** Manrope (headers), Public Sans (body), Material Symbols (icons)
- **Mobile:** Bottom tab nav with responsive grid layout
- **Cards:** Asymmetric borders, confidence bars, cost indicators, model icons

## Testing Without API Keys

The app works in "mock mode" when `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` are not set:
- Agents return placeholder responses with 0 cost
- Full UI flow is functional
- Streaming still works

## Next Steps

1. Configure API keys to enable real agent execution
2. Test each council type (Selves, Ideas, Innovation)
3. Try chaining (Innovation → Ideas → Selves)
4. Build custom councils from the agent pool
5. Monitor token usage and costs in session view

## Production Notes

- SQLite database stored at `/home/openclaw/.openclaw/workspace/council-platform/council.db`
- For production: consider PostgreSQL, add auth, enable HTTPS
- SSE connection timeout is 120s; adjust as needed
- Token pricing reflects current Anthropic/Google rates; update in `providers/`

## Known Issues / TODO

- Custom council builder needs backend support for arbitrary agent combinations (current: use canonical templates)
- PDF export not yet implemented (recommend client-side printing)
- Council chaining needs UI refinement for multi-phase councils
- Mobile streaming UI could use optimization

---

**Built with:** FastAPI, Jinja2, SQLite, SSE, Dark Mode, Design System  
**Status:** MVP ready for testing  
**Budget:** Take your time, get this right. This is a flagship product.
