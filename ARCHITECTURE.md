# Council Platform — Unified Architecture Spec

**Version:** 1.0  
**Date:** 2026-03-28  
**Status:** Draft — ready for review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Three Councils](#2-the-three-councils)
3. [Unified Platform Architecture](#3-unified-platform-architecture)
4. [Council Mixing and Custom Configurations](#4-council-mixing-and-custom-configurations)
5. [Additional Council Configurations](#5-additional-council-configurations)
6. [The Agent Pool Model](#6-the-agent-pool-model)
7. [Technical Architecture](#7-technical-architecture)
8. [UX Design](#8-ux-design)
9. [Migration Path](#9-migration-path)
10. [Open Questions](#10-open-questions)

---

## 1. Executive Summary

The Council Platform unifies three distinct multi-agent deliberation systems under a single application. Each council type serves a fundamentally different cognitive purpose:

- **Council of Selves** — introspective. Inner parts dialogue about decisions through an IFS therapy lens. The question: *"What do I actually want?"*
- **Idea Council** — evaluative. External agents stress-test a formed proposal. The question: *"Is this idea any good?"*
- **Innovation Council** — generative. Agents explore a theme and surface opportunities that don't exist yet. The question: *"What's hiding in this space?"*

The platform is not three apps sharing a nav bar. It's a single system where **the unit of work is a deliberation** — a structured multi-perspective examination of a question — and the council type determines *how* that deliberation is conducted.

Beyond fixed councils, the platform introduces **council mixing** (agents from different councils in one session), **council chaining** (output of one council feeds the next), and ultimately an **agent pool model** where the user composes bespoke councils from a library of ~20 archetypes.

---

## 2. The Three Councils

### 2.1 Council of Selves (Existing)

**Purpose:** Self-knowledge through structured inner dialogue.  
**Metaphor:** The Chamber.  
**Agents:** The Engine, The Inspector, The Shield, The Architect, The Night Worker, The Delegator.  
**Mode:** Dialogic — parts speak *to each other*, not just about the topic.  
**Output:** A mirror view showing what each part thinks, where they conflict, and what the Self (the observing awareness above the parts) notices.  
**Key feature:** Confidence scores per part. Parts can have high conviction but low confidence — they *feel* strongly but acknowledge uncertainty.

**What makes it distinct:** This is the only council where the agents represent *you*. They're not external evaluators or creative generators — they're fragments of a person's inner world having a conversation. The therapeutic framing (IFS) means the goal isn't a verdict but *understanding*: what part of me is activated by this decision? What's the fear underneath the objection? What does The Shield think it's protecting?

### 2.2 Idea Council (Spec exists — PLAYBOOK.md)

**Purpose:** Convergent evaluation of a formed proposal.  
**Metaphor:** The Arena.  
**Agents:** Prosecutor, Pivot Artist, Operator, Customer Voice, Contrarian.  
**Mode:** Parallel evaluation → synthesis. Agents don't talk to each other — they each deliver a brief, and a synthesiser finds the signal.  
**Output:** Synthesis document with convergences, tensions, blind spots, emergent insights, and three questions to sit with.  
**Key feature:** Confidence tags per claim ([HIGH], [MODERATE], [SPECULATIVE]). Optional dual-synthesiser mode at different temperatures.

**What makes it distinct:** Strictly convergent. Takes an idea that *exists* and narrows toward truth about it. The agents are adversarial in function — even the Pivot Artist, who is generative, is generative *in service of evaluating* the original idea (by showing what else it could be). The output is deliberately not a verdict but questions, because premature closure kills good ideas as surely as uncritical enthusiasm does.

### 2.3 Innovation Council (Spec exists — innovation-council-spec.md)

**Purpose:** Divergent opportunity generation from a theme.  
**Metaphor:** The Lab.  
**Agents:** Archaeologist, Void Reader, Collision Artist, Anthropologist, Signal Hunter.  
**Mode:** Two-phase: diverge (parallel, independent) → collide (sequential cross-pollination) → crystallise (synthesis).  
**Output:** Opportunity Map with 3 opportunities, an undercurrent (meta-pattern), and a discomfort (frame-challenging observation).  
**Key feature:** Multi-model (Claude + Gemini) for structural cognitive diversity. Energy parameter (provocation / prototypable / strategic / weird).

**What makes it distinct:** The only council designed for *generation*. It doesn't evaluate what exists — it produces what doesn't exist yet. The two-phase structure is critical: Phase 1 maximises independent divergence, Phase 2 forces cross-pollination that produces emergent opportunities no single agent would generate. The multi-model requirement isn't a nice-to-have — same-model "diversity" is prompt engineering, not epistemic diversity.

---

## 3. Unified Platform Architecture

### 3.1 Design Principle: One Platform, Three Modes

The platform should feel like **one thing with three modes**, not three apps stitched together. The analogy: a professional camera has Manual, Aperture Priority, and Shutter Priority modes. Same camera, same controls, same design language — but fundamentally different operational modes that produce different results.

The unifying concept: **deliberation**. Every session on the platform is a deliberation — a structured, multi-perspective examination of a question. What varies is:

| Dimension | Council of Selves | Idea Council | Innovation Council |
|---|---|---|---|
| **Input** | A decision or dilemma | A formed proposal | A theme or territory |
| **Agents** | Inner parts (personal) | External evaluators | Creative generators |
| **Mode** | Dialogic (parts converse) | Parallel → synthesis | Diverge → collide → crystallise |
| **Output** | Mirror (self-understanding) | Synthesis (convergent truth) | Opportunity Map (divergent possibilities) |
| **Emotional register** | Therapeutic, gentle | Adversarial, rigorous | Exploratory, provocative |
| **Models** | Single (Claude) | Single (Claude) | Multi (Claude + Gemini) |

### 3.2 Navigation Structure

**Current:** Council of Selves has a sidebar with: Council Chamber, Sessions, Mirror View, Inner Parts.

**Proposed:** The platform introduces a top-level council selector with a shared sidebar that adapts per council type.

```
┌─────────────────────────────────────────────────┐
│  🏛️ Council Platform              [user avatar] │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│  MODE    │                                      │
│  ────    │                                      │
│  🪞 Selves  │        [Main Content Area]        │
│  ⚔️ Ideas   │                                   │
│  🔬 Lab     │                                   │
│  🎛️ Custom  │                                   │
│          │                                      │
│  ────────│                                      │
│  CONTEXT │                                      │
│  ────    │                                      │
│  [adapts │                                      │
│   per    │                                      │
│   mode]  │                                      │
│          │                                      │
│  ────────│                                      │
│  RECENT  │                                      │
│  Sessions│                                      │
│  ────    │                                      │
│  [unified│                                      │
│   history│                                      │
│   all    │                                      │
│   types] │                                      │
│          │                                      │
└──────────┴──────────────────────────────────────┘
```

**Sidebar structure:**

1. **Mode selector** (top) — switches between council types. Each has its own icon and colour accent (teal for Selves, amber for Ideas, violet for Lab, slate for Custom).
2. **Context panel** (middle) — adapts to the selected mode:
   - *Selves:* Inner Parts list with confidence indicators
   - *Ideas:* Agent roster (Prosecutor, Pivot Artist, etc.) with status
   - *Lab:* Agent roster + Energy selector + Model indicators
   - *Custom:* Agent pool browser / saved configurations
3. **Recent sessions** (bottom) — unified across all council types, with type badges. Filterable.

### 3.3 Home Page

The current home page is Council of Selves-specific. The platform home needs to serve three purposes: orient new users, provide quick-start for returning users, and surface interesting patterns across deliberations.

**Proposed home layout:**

```
┌───────────────────────────────────────────────┐
│                                               │
│     What's on your mind?                      │
│     ┌───────────────────────────────────┐     │
│     │ Type a question, idea, or theme...│     │
│     └───────────────────────────────────┘     │
│                                               │
│     The platform suggests the right council   │
│     based on your input. You can override.    │
│                                               │
├───────────┬───────────┬───────────────────────┤
│           │           │                       │
│  🪞 The    │  ⚔️ The    │  🔬 The               │
│  Chamber  │  Arena    │  Lab                  │
│           │           │                       │
│  "What do │  "Is this │  "What's hiding       │
│  I really │  idea any │  in this space?"      │
│  want?"   │  good?"   │                       │
│           │           │                       │
│  [Enter]  │  [Enter]  │  [Enter]              │
│           │           │                       │
├───────────┴───────────┴───────────────────────┤
│                                               │
│  Recent Deliberations                         │
│  ┌─────────────────────────────────────────┐  │
│  │ 🪞 "Should I take the new role?"  2h ago│  │
│  │ ⚔️ "Nemesis product idea"       yesterday│  │
│  │ 🔬 "Future of personal finance"   Mar 26│  │
│  └─────────────────────────────────────────┘  │
│                                               │
└───────────────────────────────────────────────┘
```

**The smart input bar** is the killer feature of the home page. The user types naturally — "Should I quit my job?", "I have an idea for a marketplace", "What opportunities exist in AI agents?" — and the platform classifies it:

- Personal decision / dilemma → suggests Council of Selves
- Formed idea / proposal → suggests Idea Council  
- Open theme / exploratory → suggests Innovation Council
- Ambiguous → shows all three options with a brief explanation

This removes the friction of choosing a council type and teaches users the distinction through experience.

### 3.4 Shared Design Language

The existing teal/white aesthetic becomes the **platform base**. Each council type gets a subtle colour accent that runs through its interface without breaking the overall cohesion:

| Council | Accent | Rationale |
|---|---|---|
| Selves | Teal (existing) | Continuity, calm, introspective |
| Ideas | Warm amber | Arena energy, focused intensity |
| Lab | Deep violet | Creative, mysterious, exploratory |
| Custom | Slate grey | Neutral — the canvas, not the paint |

The accent appears in: the mode indicator, agent cards, session badges, and progress indicators. Everything else remains the shared design system — same typography, same card structure, same spacing, same confidence bars.

**Confidence bars** are a unifying UI element across all three councils. They mean different things per context:
- *Selves:* How confident is this part in its position?
- *Ideas:* How confident is the agent in this claim? (HIGH/MODERATE/SPECULATIVE mapped to %)
- *Lab:* How promising is this opportunity relative to the others?

---

## 4. Council Mixing and Custom Configurations

This is where it gets genuinely interesting.

### 4.1 Can You Mix Agents From Different Councils?

**Yes, but the combinations need to be intentional, not arbitrary.**

The agents across the three councils represent three fundamentally different cognitive functions:

- **Selves agents** = subjective, personal, emotional. They represent *your* inner world.
- **Idea agents** = evaluative, external, convergent. They represent *the world's* response to your idea.
- **Innovation agents** = generative, exploratory, divergent. They represent *what could exist*.

Mixing them produces new capabilities:

**Example 1: Personal-Evaluative Mix**
*The Engine (Selves) + The Prosecutor (Ideas) + The Anthropologist (Innovation)*

Use case: "I want to start a business, but I'm not sure if that's ambition or escapism."

- The Engine examines the drive behind the desire
- The Prosecutor stress-tests the business case
- The Anthropologist observes the user's actual behaviour patterns around work

This combination doesn't exist in any single council. It produces a *personal evaluation* — not just "is the idea good?" (Idea Council) or "what do I feel?" (Selves) but "is this desire authentic AND is the vehicle viable?"

**Example 2: Evaluative-Generative Mix**
*The Contrarian (Ideas) + The Collision Artist (Innovation) + The Void Reader (Innovation)*

Use case: "This product is failing. What am I not seeing?"

- The Contrarian challenges the premise ("maybe the product isn't failing — maybe you're measuring wrong")
- The Void Reader identifies what's missing from the current approach
- The Collision Artist forces new combinations from existing assets

This is neither evaluation nor innovation — it's **diagnostic creativity**: understanding what's wrong while simultaneously generating alternatives.

**Example 3: Full Spectrum**
*The Shield (Selves) + The Operator (Ideas) + The Signal Hunter (Innovation)*

Use case: "Should I invest in this opportunity?"

- The Shield surfaces the fear and protective instincts
- The Operator does a cold-eyed operational assessment
- The Signal Hunter checks timing — is the signal real or noise?

This produces an **aligned investment decision**: emotionally grounded, operationally realistic, and temporally aware.

### 4.2 Can Councils Chain?

**Yes, and this is the platform's most powerful capability.**

The natural pipeline:

```
Innovation Council → Idea Council → Council of Selves
  "What opportunities     "Is the best       "Does this align
   exist in X?"           one viable?"        with who I am?"
```

**Implementation:**

Each council session produces structured output. The chaining mechanism converts one council's output into the next council's input:

1. **Innovation → Idea:** The Opportunity Map's three opportunities become three separate Idea Council sessions (or the user picks one). The Innovation Council's opportunity description becomes the Idea Council's input spec. Context carries forward — the Idea Council agents know this originated from an Innovation session and can reference the lineage.

2. **Idea → Selves:** The Idea Council's synthesis — particularly the "three questions to sit with" — becomes the input for Council of Selves. The inner parts respond not to the raw idea but to the evaluated version: "The council thinks this is strong but operationally heavy. How do I feel about that?"

3. **Selves → back to anything:** If the Council of Selves reveals that the real question is different from what was asked ("I don't actually want to build a business — I want to feel competent"), that reframe can feed back into a new Innovation session with the *real* theme.

**Chain UI:**

Sessions that are part of a chain show a visual lineage:

```
🔬 "AI opportunities"  →  ⚔️ "Financial Mirror"  →  🪞 "Do I want this?"
   [Innovation]             [Idea evaluation]         [Personal alignment]
   3 opportunities          Strong with caveats       The Engine says yes,
   identified               Trust = hard part          The Shield says wait
```

The user can enter the chain at any point, skip steps, or re-run a step with different parameters.

### 4.3 Can Users Build Custom Councils?

**Yes — this is the endgame of the platform.**

Once the agent pool exists (see Section 6), the user can:

1. **Pick agents** — select 3-7 agents from the full pool
2. **Set the mode** — dialogic (agents converse), parallel (independent briefs → synthesis), or phased (diverge → collide)
3. **Configure interaction** — which agents see each other's output? In what order?
4. **Save as a preset** — name it, reuse it, share it

**Example custom council: "The Launch Council"**
Agents: The Operator (Ideas), The Signal Hunter (Innovation), The Engine (Selves), The Anthropologist (Innovation), The Prosecutor (Ideas)

Mode: Parallel → synthesis. Purpose: pre-launch decision-making for a product. Combines operational realism, market timing, personal drive, user empathy, and risk assessment.

### 4.4 What Emerges From Combinations

The most interesting emergent property: **tension between agent ontologies**.

Selves agents treat the user as a collection of parts with needs and fears. Idea agents treat the world as a system of market forces and constraints. Innovation agents treat reality as a space of latent possibilities.

When you put them together, these *frames* collide — and the collision is the insight:

- The Prosecutor says "this won't work because of X."
- The Engine says "but I *need* this to work — what's driving that?"
- The Collision Artist says "what if X isn't a problem but a feature?"

No single council produces that three-way tension. The combination doesn't just mix perspectives — it creates a **meta-perspective** that none of the individual councils can access.

This is the platform's genuine novelty: not multi-agent deliberation (that exists) but **multi-ontology deliberation** — agents that don't just disagree about facts but disagree about *what kind of thing the question is*.

---

## 5. Additional Council Configurations

### 5.1 Strategy Council

**Purpose:** Long-horizon planning with competing strategic frames.  
**Metaphor:** The War Room.  
**When to use:** "Where should I be in 5 years?" / "How should this company position itself?"

**Agents:**

| Agent | Function |
|---|---|
| **The Cartographer** | Maps the current landscape — where are we, what are the forces, what's the terrain? |
| **The Historian** | Pattern-matches against historical precedent — what happened when others faced similar choices? |
| **The Futurist** | Projects forward from weak signals — what's the landscape in 3/5/10 years? |
| **The Economist** | Models resource allocation and trade-offs — what does each path cost, and what do we give up? |
| **The Saboteur** | Pre-mortems every strategy — "assume this failed, here's why" |

**Mode:** Phased. Phase 1: each agent produces an independent strategic brief. Phase 2: The Saboteur pre-mortems each strategy, then the remaining agents defend or revise. Phase 3: Synthesis produces 2-3 strategic paths with explicit trade-offs.

**Why it's not covered by existing councils:** The Idea Council evaluates a formed proposal. The Strategy Council operates *before* there's a proposal — it's about choosing which direction to form proposals *in*. The Innovation Council generates opportunities but doesn't prioritise across time horizons or model resource constraints.

### 5.2 Debug Council

**Purpose:** Diagnose what went wrong and why.  
**Metaphor:** The Autopsy Room.  
**When to use:** "The launch failed." / "I keep having the same argument." / "This project is stuck."

**Agents:**

| Agent | Function |
|---|---|
| **The Coroner** | Establishes the facts — what actually happened, in what sequence? Separates evidence from narrative. |
| **The Systems Thinker** | Maps feedback loops and structural causes — not "who's to blame" but "what system produced this?" |
| **The Therapist** | Examines the emotional and interpersonal dynamics — what wasn't said? What was avoided? |
| **The Contrarian** (borrowed) | Challenges the premise — "are you sure this was actually a failure?" |
| **The Architect** (borrowed from Selves) | Looks at the structural/design decisions that led here — what was the plan, and where did reality diverge? |

**Mode:** Sequential. The Coroner goes first (establish facts). Then Systems Thinker + Therapist in parallel (structural and emotional analysis). Then Contrarian (challenge the frame). Then Architect (what to rebuild). This order matters — diagnosis before treatment.

**Key innovation:** The Debug Council borrows agents from other councils. The Contrarian from Ideas and The Architect from Selves serve different functions here than in their home contexts. This demonstrates the pool model working.

### 5.3 Due Diligence Council

**Purpose:** Evaluate an investment, acquisition, partnership, or major commitment.  
**Metaphor:** The Tribunal.  
**When to use:** "Should I invest in X?" / "Should we acquire this company?" / "Should I take this job offer?"

**Agents:**

| Agent | Function |
|---|---|
| **The Auditor** | Financial and quantitative analysis — what do the numbers actually say? |
| **The Investigator** | Background and reputation — what's the track record? What aren't they telling you? |
| **The Modeller** | Scenario analysis — best case, base case, worst case, and the case nobody's modelling |
| **The Customer Voice** (borrowed) | If this is a business: would the customer care? If personal: would future-you thank present-you? |
| **The Shield** (borrowed from Selves) | What are you afraid of? What's the cost of being wrong? What's the cost of not acting? |

**Mode:** Parallel → synthesis, but with a unique output structure: a **conviction score** (0-100) that represents the council's aggregate confidence, alongside the qualitative synthesis. The conviction score isn't a recommendation — it's a legible summary of how much collective confidence exists.

### 5.4 Ethics Council

**Purpose:** Examine a decision through multiple ethical and value frameworks.  
**Metaphor:** The Hearing.  
**When to use:** "Is this the right thing to do?" / "What are the ethical implications of X?"

**Agents:**

| Agent | Function |
|---|---|
| **The Consequentialist** | Outcomes-focused — what happens as a result? Who benefits, who's harmed, over what time horizon? |
| **The Deontologist** | Principles-focused — regardless of outcome, is this action right? What rules or duties does it violate? |
| **The Virtue Ethicist** | Character-focused — what kind of person does this action make you? What habits does it reinforce? |
| **The Stakeholder** | Perspective-taking — who's affected that isn't in the room? Whose voice is missing? |
| **The Pragmatist** | Reality-focused — given the constraints of the actual situation, what's the least-bad option? |

**Mode:** Dialogic (like Council of Selves). The agents genuinely debate — they don't just deliver independent briefs. Ethical questions are fundamentally about tensions between frameworks, and the dialogue makes those tensions visible.

### 5.5 The Unnamed One: The Integration Council

**Purpose:** When you have *too many inputs* and need to find coherence.  
**Metaphor:** The Loom.  
**When to use:** After running multiple councils. After gathering lots of advice. When you have 47 tabs open and can't think straight.

This council doesn't generate new material. It takes everything you already have — council outputs, notes, research, half-formed thoughts — and weaves it into a coherent picture. 

**Agents:**

| Agent | Function |
|---|---|
| **The Weaver** | Finds threads that connect disparate inputs — what's the through-line? |
| **The Editor** | Cuts what doesn't matter — what can you safely ignore? |
| **The Narrator** | Constructs the story — given everything, what's the *narrative* of where you are and where you're going? |

Three agents, not five. Deliberately small. This council's virtue is compression, not expansion.

---

## 6. The Agent Pool Model

### 6.1 The Vision

Instead of fixed councils with fixed rosters, the platform maintains a **pool of agent archetypes**. Each archetype has:

- A cognitive function (what it *does* to the problem space)
- A personality (how it communicates)
- A prompt template (the system prompt that instantiates it)
- A home council (where it originated, but it can serve elsewhere)
- Tags (evaluative, generative, introspective, adversarial, etc.)

The user (or the platform's AI) composes the right council for each situation by selecting agents from the pool.

### 6.2 The Universal Pool (~25 Archetypes)

Organised by cognitive function:

#### Evaluative (convergent — narrow toward truth)

| # | Archetype | Function | Home Council |
|---|---|---|---|
| 1 | **The Prosecutor** | Finds structural flaws, kill shots | Idea |
| 2 | **The Operator** | Reality-checks cost, ops, execution | Idea |
| 3 | **The Customer Voice** | "Would I actually buy/want this?" | Idea |
| 4 | **The Contrarian** | Challenges the premise itself | Idea |
| 5 | **The Auditor** | Quantitative/financial analysis | Due Diligence |
| 6 | **The Investigator** | Background, track record, hidden risks | Due Diligence |
| 7 | **The Saboteur** | Pre-mortems — "assume this failed" | Strategy |

#### Generative (divergent — expand the possibility space)

| # | Archetype | Function | Home Council |
|---|---|---|---|
| 8 | **The Pivot Artist** | "What else could this be?" | Idea |
| 9 | **The Archaeologist** | Cross-domain structural analogues | Innovation |
| 10 | **The Void Reader** | Sees what's missing, negative space | Innovation |
| 11 | **The Collision Artist** | Forces provocative juxtapositions | Innovation |
| 12 | **The Signal Hunter** | Weak signals from the fringe | Innovation |
| 13 | **The Futurist** | Projects forward from current trends | Strategy |
| 14 | **The Cartographer** | Maps the current landscape | Strategy |

#### Introspective (self-knowledge — illuminate inner dynamics)

| # | Archetype | Function | Home Council |
|---|---|---|---|
| 15 | **The Engine** | Drive, ambition, wants | Selves |
| 16 | **The Inspector** | Standards, quality, judgment | Selves |
| 17 | **The Shield** | Protection, fear, risk aversion | Selves |
| 18 | **The Architect** | Planning, structure, design | Selves |
| 19 | **The Night Worker** | Subconscious processing, intuition | Selves |
| 20 | **The Delegator** | Capacity, boundaries, saying no | Selves |

#### Relational (perspective-taking — represent other viewpoints)

| # | Archetype | Function | Home Council |
|---|---|---|---|
| 21 | **The Anthropologist** | Observes actual human behaviour | Innovation |
| 22 | **The Stakeholder** | Represents affected parties not in the room | Ethics |
| 23 | **The Therapist** | Emotional/interpersonal dynamics | Debug |

#### Integrative (synthesis — compress toward coherence)

| # | Archetype | Function | Home Council |
|---|---|---|---|
| 24 | **The Weaver** | Finds threads connecting disparate inputs | Integration |
| 25 | **The Narrator** | Constructs story from chaos | Integration |

#### Meta (structural — operate on the process itself)

| # | Archetype | Function | Home Council |
|---|---|---|---|
| 26 | **The Systems Thinker** | Maps feedback loops, structural causes | Debug |
| 27 | **The Modeller** | Scenarios — best/base/worst/unmodelled | Due Diligence |

### 6.3 AI-Suggested Compositions

The platform's highest-value feature may be **automatic council composition**. Given a user's input, the AI:

1. Classifies the question type (decision, evaluation, exploration, diagnosis, ethical dilemma, strategic choice)
2. Identifies the cognitive functions needed
3. Selects 3-7 agents from the pool
4. Suggests a mode (dialogic, parallel, phased)
5. Presents the suggested council to the user, who can accept, modify, or override

**Example:**
> User: "My co-founder wants to pivot the company. I'm not sure."
> 
> Platform suggests: **Custom Council (5 agents)**
> - The Engine (what do you want from this company?)
> - The Shield (what are you afraid of losing?)
> - The Operator (what does the pivot actually cost?)
> - The Contrarian (is the pivot the real question, or is this about the co-founder relationship?)
> - The Futurist (where does the market go if you pivot vs. don't?)
> 
> Mode: Dialogic (these agents should argue, not deliver independent briefs)

The user sees this as a suggestion, not a prescription. They can swap agents, add one, remove one, change the mode. Over time, the platform learns which compositions the user prefers and which produce the most valued outputs.

### 6.4 Saved Configurations and Templates

Users can save custom compositions as reusable templates:

```json
{
  "name": "My Launch Council",
  "agents": ["operator", "signal-hunter", "engine", "anthropologist", "prosecutor"],
  "mode": "parallel",
  "description": "Pre-launch reality check — ops + timing + drive + users + risks"
}
```

The platform ships with the three canonical councils as pre-built templates. Community-shared templates could become a thing later (marketplace of council configurations), but that's post-v1.

---

## 7. Technical Architecture

### 7.1 Current Stack

- **Backend:** FastAPI (Python)
- **Templates:** Jinja2 with server-side rendering
- **Database:** SQLite
- **UI:** Teal/white design, HTML/CSS/JS, confidence bars
- **AI:** Direct API calls to Anthropic (Claude)

### 7.2 Database Schema

**Unified session model** — one `sessions` table with a `council_type` field, not separate tables per council.

```sql
-- Core tables

CREATE TABLE agents (
    id          TEXT PRIMARY KEY,        -- e.g. "prosecutor", "the-engine"
    name        TEXT NOT NULL,           -- "The Prosecutor"
    description TEXT,
    system_prompt TEXT NOT NULL,
    cognitive_function TEXT,             -- "evaluative", "generative", "introspective"
    home_council TEXT,                   -- "idea", "innovation", "selves"
    icon        TEXT,                    -- emoji
    default_model TEXT DEFAULT 'claude', -- "claude", "gemini", "any"
    tags        TEXT,                    -- JSON array: ["adversarial", "convergent"]
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE council_templates (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,           -- "Idea Council", "My Launch Council"
    type        TEXT NOT NULL,           -- "canonical", "custom"
    agent_ids   TEXT NOT NULL,           -- JSON array of agent IDs
    mode        TEXT NOT NULL,           -- "dialogic", "parallel", "phased"
    phase_config TEXT,                   -- JSON: phase definitions for phased mode
    description TEXT,
    icon        TEXT,
    accent_color TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,
    council_template_id TEXT,            -- which council config was used
    council_type TEXT NOT NULL,          -- "selves", "idea", "innovation", "custom"
    title       TEXT,
    input_text  TEXT NOT NULL,           -- the question/idea/theme
    input_meta  TEXT,                    -- JSON: energy, constraints, context (Innovation)
    status      TEXT DEFAULT 'active',   -- "active", "completed", "chained"
    chain_parent_id TEXT,               -- if part of a chain, which session preceded this
    chain_position INTEGER,             -- position in chain (1, 2, 3...)
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (council_template_id) REFERENCES council_templates(id),
    FOREIGN KEY (chain_parent_id) REFERENCES sessions(id)
);

CREATE TABLE session_agents (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    phase       INTEGER DEFAULT 1,       -- which phase this agent participates in
    model_used  TEXT,                    -- "claude-sonnet", "gemini-1.5-pro", etc.
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE deliberation_turns (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    phase       INTEGER DEFAULT 1,
    turn_order  INTEGER,                -- for sequential/dialogic modes
    content     TEXT NOT NULL,           -- the agent's output (markdown)
    confidence  REAL,                   -- 0.0 - 1.0, nullable
    model_used  TEXT,
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    cost_usd    REAL,
    started_at  TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE syntheses (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    content     TEXT NOT NULL,           -- the synthesis output (markdown)
    synthesis_type TEXT,                 -- "convergent", "opportunity_map", "mirror"
    model_used  TEXT,
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    cost_usd    REAL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indices
CREATE INDEX idx_sessions_type ON sessions(council_type);
CREATE INDEX idx_sessions_chain ON sessions(chain_parent_id);
CREATE INDEX idx_turns_session ON deliberation_turns(session_id);
CREATE INDEX idx_turns_phase ON deliberation_turns(session_id, phase);
```

**Why unified, not separate:**

1. Cross-council queries ("show me all sessions about finance") work without JOINs across tables
2. Chaining is a simple foreign key, not a cross-table reference
3. The `council_template_id` captures which configuration was used, so you don't need the table structure to encode the council type
4. Custom councils would need their own table otherwise — the unified model handles them natively
5. Analytics across council types (cost tracking, usage patterns) are trivial

### 7.3 API Layer

```python
# FastAPI route structure

app = FastAPI(title="Council Platform")

# ── Home & Navigation ────────────────────────────
@app.get("/")                          # Platform home
@app.get("/sessions")                  # All sessions, filterable by type
@app.get("/sessions/{session_id}")     # Single session view

# ── Council of Selves ────────────────────────────
@app.get("/selves")                    # Selves landing
@app.get("/selves/chamber")            # Enter the Chamber
@app.post("/selves/deliberate")        # Start a deliberation
@app.get("/selves/mirror/{session_id}") # Mirror view for a session
@app.get("/selves/parts")             # Manage inner parts

# ── Idea Council ─────────────────────────────────
@app.get("/ideas")                     # Ideas landing
@app.get("/ideas/arena")               # Enter the Arena
@app.post("/ideas/evaluate")           # Start an evaluation
@app.get("/ideas/synthesis/{session_id}") # Synthesis view

# ── Innovation Council ───────────────────────────
@app.get("/lab")                       # Lab landing
@app.get("/lab/explore")               # Enter the Lab
@app.post("/lab/innovate")             # Start an exploration
@app.get("/lab/map/{session_id}")      # Opportunity Map view

# ── Custom Councils ──────────────────────────────
@app.get("/custom")                    # Council builder
@app.post("/custom/compose")           # Create a custom council
@app.post("/custom/deliberate")        # Run a custom council
@app.get("/custom/templates")          # Saved templates

# ── Agent Pool ───────────────────────────────────
@app.get("/agents")                    # Browse all agents
@app.get("/agents/{agent_id}")         # Agent detail

# ── Chains ───────────────────────────────────────
@app.get("/chains/{chain_id}")         # View a chain of sessions
@app.post("/chains/continue")          # Continue a chain with next council

# ── Streaming ────────────────────────────────────
@app.get("/stream/{session_id}")       # SSE endpoint for real-time results
```

### 7.4 Agent Execution Architecture

**Recommendation: Direct API calls, not OpenClaw sub-agents.**

Rationale:
- Lower latency — no sub-agent spawning overhead
- Fine-grained control over model selection per agent
- Streaming control — can SSE individual agent completions
- Cost tracking — can measure tokens and cost per agent directly
- The web app is the orchestrator; it doesn't need another orchestration layer

**Execution engine design:**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import anthropic
import google.generativeai as genai

@dataclass
class AgentConfig:
    agent_id: str
    system_prompt: str
    model: str          # "claude-sonnet-4-20250514", "gemini-1.5-pro", etc.
    provider: str       # "anthropic", "google"
    temperature: float = 0.7

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

class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, config: AgentConfig, messages: list[dict]) -> AgentResult:
        ...

class AnthropicProvider(ModelProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate(self, config: AgentConfig, messages: list[dict]) -> AgentResult:
        # Implementation with streaming support
        ...

class GoogleProvider(ModelProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
    
    async def generate(self, config: AgentConfig, messages: list[dict]) -> AgentResult:
        ...

class CouncilOrchestrator:
    """Runs a council session — handles parallel, sequential, and phased execution."""
    
    def __init__(self, providers: dict[str, ModelProvider]):
        self.providers = providers
    
    async def run_parallel(
        self, 
        agents: list[AgentConfig], 
        input_text: str,
        on_complete: callable  # SSE callback per agent completion
    ) -> list[AgentResult]:
        """Run all agents in parallel. Used for Phase 1 of all councils."""
        tasks = [
            self._run_agent(agent, input_text, on_complete)
            for agent in agents
        ]
        return await asyncio.gather(*tasks)
    
    async def run_sequential(
        self,
        agents: list[AgentConfig],
        input_text: str,
        prior_results: list[AgentResult],
        on_complete: callable
    ) -> list[AgentResult]:
        """Run agents sequentially, each seeing prior outputs. 
        Used for Phase 2 of Innovation Council and dialogic modes."""
        results = list(prior_results)
        for agent in agents:
            context = self._build_context(input_text, results)
            result = await self._run_agent(agent, context, on_complete)
            results.append(result)
        return results
    
    async def run_phased(
        self,
        phase_configs: list[PhaseConfig],
        input_text: str,
        on_complete: callable
    ) -> list[list[AgentResult]]:
        """Run a multi-phase council. Each phase can be parallel or sequential."""
        all_results = []
        for phase in phase_configs:
            if phase.mode == "parallel":
                results = await self.run_parallel(
                    phase.agents, input_text, on_complete
                )
            else:
                results = await self.run_sequential(
                    phase.agents, input_text, 
                    [r for phase_results in all_results for r in phase_results],
                    on_complete
                )
            all_results.append(results)
        return all_results
```

### 7.5 Streaming (SSE)

Real-time results as each agent completes. The UI updates progressively — the user sees agent cards fill in one by one, rather than waiting for all agents to finish.

```python
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

@app.get("/stream/{session_id}")
async def stream_session(session_id: str):
    async def event_generator():
        async for event in session_event_bus.subscribe(session_id):
            match event.type:
                case "agent_started":
                    yield {
                        "event": "agent_started",
                        "data": json.dumps({
                            "agent_id": event.agent_id,
                            "phase": event.phase
                        })
                    }
                case "agent_streaming":
                    # Token-by-token streaming for the current agent
                    yield {
                        "event": "agent_token",
                        "data": json.dumps({
                            "agent_id": event.agent_id,
                            "token": event.token
                        })
                    }
                case "agent_completed":
                    yield {
                        "event": "agent_completed",
                        "data": json.dumps({
                            "agent_id": event.agent_id,
                            "content": event.content,
                            "confidence": event.confidence,
                            "cost_usd": event.cost_usd
                        })
                    }
                case "phase_completed":
                    yield {
                        "event": "phase_completed",
                        "data": json.dumps({"phase": event.phase})
                    }
                case "synthesis_started":
                    yield {"event": "synthesis_started", "data": "{}"}
                case "synthesis_completed":
                    yield {
                        "event": "synthesis_completed",
                        "data": json.dumps({
                            "content": event.content,
                            "cost_usd": event.total_cost
                        })
                    }
                case "session_completed":
                    yield {"event": "session_completed", "data": "{}"}
                    break
    
    return EventSourceResponse(event_generator())
```

**UI behaviour during streaming:**

1. Session starts → all agent cards appear in "waiting" state (greyed, pulsing dot)
2. Agent starts → card transitions to "thinking" state (animated border in council accent colour)
3. Tokens stream → card shows content appearing in real-time (typewriter effect)
4. Agent completes → card solidifies, confidence bar fills, cost displays in corner
5. Phase completes → visual separator, next phase begins
6. Synthesis starts → dedicated synthesis card animates in
7. Session complete → all cards lock, "View Full Deliberation" and "Chain →" buttons appear

### 7.6 Multi-Model Implementation

The Innovation Council spec requires Claude + Gemini. Here's how this works practically:

```python
# Model assignment per agent role
INNOVATION_COUNCIL_MODELS = {
    "archaeologist": {"phase1": "gemini-1.5-pro", "phase2": "claude-sonnet"},
    "void-reader":   {"phase1": "claude-sonnet",   "phase2": "gemini-1.5-pro"},
    "collision-artist": {"phase1": "gemini-1.5-pro", "phase2": "claude-sonnet"},
    "anthropologist": {"phase1": "claude-sonnet",   "phase2": "gemini-1.5-pro"},
    "signal-hunter":  {"phase1": "gemini-1.5-pro", "phase2": "claude-sonnet"},
}

# Phase 2 alternation: if Phase 1 was Claude, Phase 2 is Gemini (and vice versa)
# Synthesis: strongest available model (currently Claude Opus or Gemini Ultra)
```

**API key management:**

```python
# Environment variables
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Config in settings
class Settings(BaseSettings):
    anthropic_api_key: str
    google_api_key: str
    default_model: str = "claude-sonnet"
    synthesis_model: str = "claude-opus"  # strongest available
```

**Prompt translation:** Claude and Gemini have different system prompt conventions. The platform maintains a prompt template per agent that's model-agnostic, plus a thin translation layer:

```python
def format_for_provider(agent: Agent, provider: str, context: str) -> dict:
    if provider == "anthropic":
        return {
            "system": agent.system_prompt,
            "messages": [{"role": "user", "content": context}]
        }
    elif provider == "google":
        return {
            "system_instruction": agent.system_prompt,
            "contents": [{"role": "user", "parts": [{"text": context}]}]
        }
```

### 7.7 Cost Tracking

Every agent execution records tokens and cost. The UI shows:

- Per-agent cost in the corner of each card (subtle, e.g. "$0.02")
- Total session cost in the session header
- A `/settings` page with running cost totals by council type and time period

```python
# Cost calculation
PRICING = {
    "claude-sonnet": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-opus":   {"input": 15.0 / 1_000_000, "output": 75.0 / 1_000_000},
    "gemini-1.5-pro": {"input": 1.25 / 1_000_000, "output": 5.0 / 1_000_000},
    "gemini-ultra":  {"input": 7.0 / 1_000_000, "output": 21.0 / 1_000_000},
}

def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    rates = PRICING[model]
    return (tokens_in * rates["input"]) + (tokens_out * rates["output"])
```

---

## 8. UX Design

### 8.1 Scaling to Multiple Council Types

The risk: clutter. Three council types, each with five agents, means fifteen agent cards competing for attention — plus custom councils could add more.

**Design principles:**

1. **Progressive disclosure.** The home page shows three doors. You walk through one. Inside, you see only what's relevant to that council type. The platform never shows all agents at once unless you're in the pool browser.

2. **Consistent card anatomy.** Every agent card, regardless of council, has the same structure:
   ```
   ┌─────────────────────────┐
   │ 🔭 The Archaeologist     │
   │ Cross-domain patterns    │
   │ ━━━━━━━━━━━━━━━━ 78%    │  ← confidence bar
   │                         │
   │ [Content when complete]  │
   │                         │
   │              $0.03 • ◉  │  ← cost + model indicator
   └─────────────────────────┘
   ```
   The bar colour and model indicator (◉ = Claude, ◈ = Gemini) are the only per-council variations.

3. **The session view is the product.** Navigation and settings are chrome. The session view — agents deliberating, results streaming in, synthesis emerging — is what the user spends 90% of their time looking at. Optimise for this view being immersive and distraction-free.

4. **Colour-coded but not colour-dependent.** The teal/amber/violet accents help distinguish council types, but every distinction is also communicated through icon and label. Accessibility first.

### 8.2 Mobile Experience

The current UI is desktop-first. Mobile needs a different layout, not a squeezed desktop layout.

**Mobile navigation:** Bottom tab bar replaces the sidebar.

```
┌──────────────────────────┐
│  🏛️ Council Platform      │
│                          │
│  [Full-width content]    │
│                          │
│                          │
│                          │
│                          │
├──────────────────────────┤
│ 🪞    ⚔️    🔬    🎛️    📋 │
│Selves Ideas  Lab Custom  All│
└──────────────────────────┘
```

**Agent cards on mobile:** Stack vertically. In parallel mode, show a compact "agent bar" at the top showing status of all agents (dot indicators: grey=waiting, pulse=thinking, green=done), with the currently-visible agent's card taking full width. Swipe left/right to move between agents.

**Streaming on mobile:** Focus on one agent at a time. Show the agent that's currently generating, with a progress indicator for the overall session at the top.

### 8.3 Spatial Metaphors

Each council type has a spatial metaphor that shapes the experience:

| Council | Metaphor | Entry Phrase | Visual Treatment |
|---|---|---|---|
| Council of Selves | The Chamber | "Enter the Chamber" | Circular arrangement of parts, warm lighting, mirrors |
| Idea Council | The Arena | "Enter the Arena" | Linear arrangement, confrontational, sharp angles |
| Innovation Council | The Lab | "Enter the Lab" | Scattered arrangement, organic, things bubbling |
| Custom | The Workshop | "Enter the Workshop" | Build-your-own, tools on the wall, assembly |
| Debug | The Autopsy Room | "Open the Case" | Clinical, sequential, evidence board |
| Strategy | The War Room | "Convene the War Room" | Map table, timeline, position markers |
| Due Diligence | The Tribunal | "Convene the Tribunal" | Formal, structured, verdict-oriented |
| Ethics | The Hearing | "Open the Hearing" | Deliberative, balanced, multiple chairs |

The metaphors are not just naming — they shape the visual layout of the session view. The Chamber is circular (parts facing each other). The Arena is linear (agents on one side, the idea on the other). The Lab is organic (ideas scattered, connections drawn between them).

### 8.4 Session Flow UX

**Starting a session (any council type):**

1. User enters text in the input bar (home page or council-specific page)
2. Platform suggests council type (if from home) or confirms agents (if from council page)
3. User can modify agent selection (add/remove/swap)
4. User clicks "Begin Deliberation"
5. Transition animation to the session view (entering the Chamber/Arena/Lab)
6. Agents appear in their arrangement, streaming begins

**During a session:**

- Each agent card fills with content as it completes
- Confidence bars animate when results arrive
- Phase transitions are visually clear (a dividing line, "Phase 2: Cross-Pollination" label)
- The user can click any agent card to expand it full-width
- A running cost counter in the header (subtle)

**After a session:**

- Full deliberation is viewable as a document (exportable as markdown/PDF)
- "Chain →" button suggests the next council type based on the output
- Session appears in the unified history with its type badge
- If it's a Council of Selves session, the Mirror View is available

### 8.5 The Mirror View (Selves-specific, but extensible)

The Mirror View is Council of Selves' signature feature — a reflective summary of what the parts revealed. But the concept generalises:

| Council | "Mirror" Equivalent | Purpose |
|---|---|---|
| Selves | Mirror View | "Here's what your parts are saying" |
| Ideas | Verdict View | "Here's where the agents landed" |
| Innovation | Opportunity Map | "Here are the three opportunities" |
| Custom | Insight View | "Here's what emerged" |

Each is a synthesised, beautifully formatted summary view that strips away the process and shows only the output. The session view shows the *deliberation*. The mirror/verdict/map shows the *result*.

---

## 9. Migration Path

### Phase 1: Foundation (Week 1-2)

1. **Database migration.** Add `council_type`, `chain_parent_id`, `council_template_id` to sessions table. Add `agents`, `council_templates`, `session_agents`, `deliberation_turns`, `syntheses` tables.
2. **Agent registry.** Seed the six Selves agents into the `agents` table. Create the "Council of Selves" template in `council_templates`.
3. **Navigation refactor.** Add the top-level council selector to the sidebar. Council of Selves remains the only active option; Ideas and Lab show as "Coming Soon."
4. **Home page.** Replace the Selves-specific home with the platform home (smart input bar, three doors, recent sessions).

**Goal:** The existing Council of Selves works exactly as before, but within the new platform shell.

### Phase 2: Idea Council (Week 3-4)

1. **Seed Idea Council agents** (Prosecutor, Pivot Artist, Operator, Customer Voice, Contrarian) into the agent registry.
2. **Build the Arena session view** — parallel agent cards → synthesis view.
3. **Implement the orchestrator** — parallel execution with SSE streaming.
4. **Synthesis agent** — reads all phase 1 outputs, produces convergent synthesis.
5. **Wire up the `/ideas/*` routes.**

**Goal:** Two functional councils. The Idea Council matches the existing Playbook spec.

### Phase 3: Innovation Council (Week 5-7)

1. **Seed Innovation Council agents** (Archaeologist, Void Reader, Collision Artist, Anthropologist, Signal Hunter).
2. **Multi-model support** — add Google provider alongside Anthropic.
3. **Phased execution** — Phase 1 (parallel) → Phase 2 (sequential cross-pollination) → Phase 3 (synthesis).
4. **Opportunity Map view** — the three opportunities, undercurrent, discomfort.
5. **Energy parameter** — provocation/prototypable/strategic/weird affects agent prompts.

**Goal:** Three functional councils. The Innovation Council matches the spec, including multi-model.

### Phase 4: Mixing and Chaining (Week 8-9)

1. **Chain UI** — "Chain →" button on completed sessions. Output-to-input conversion per council type.
2. **Custom council builder** — agent pool browser, drag-and-drop composition, mode selector.
3. **AI-suggested compositions** — classify user input, suggest agents and mode.
4. **Saved templates** — persist custom configurations.

**Goal:** The platform's unique value proposition — mixing, chaining, and custom composition — is functional.

### Phase 5: Additional Councils (Week 10+)

1. **Strategy Council, Debug Council, Due Diligence Council, Ethics Council** — each as new templates with any new agents seeded.
2. **The Integration Council** — the meta-council that synthesises across deliberations.
3. **Polish** — mobile optimisation, PDF export, cost analytics dashboard.

---

## 10. Open Questions

### Product-Level

1. **Single-user or multi-user?** The Council of Selves is deeply personal (inner parts). The Idea Council could serve a team. Does the platform have accounts and sharing, or is it a personal tool?

2. **Memory across sessions.** Should the platform remember what it's learned about the user's inner parts across sessions? A longitudinal "parts profile" could be powerful for Council of Selves. But it raises privacy and storage questions.

3. **Is this a local app or a hosted service?** The privacy sensitivity of Council of Selves (inner dialogue about personal decisions) suggests local-first. But the multi-model API calls require internet anyway. A hybrid: local SQLite database, direct API calls to providers, no intermediary server.

4. **Monetisation.** If this becomes a product: per-session pricing (pass through API costs + margin)? Subscription? Free tier with limited agents?

### Technical

5. **Agent prompt versioning.** Agent prompts will evolve. Should the session record which version of the prompt was used? (Yes — for reproducibility and to measure whether prompt changes improve output quality.)

6. **Caching.** If two Innovation Council runs use the same theme, should Phase 1 results be cached? Probably not (you want fresh generation), but the question deserves explicit answering.

7. **Rate limiting.** Running 5 agents in parallel hits API rate limits quickly. The orchestrator needs backoff/retry logic, and the UI needs to handle partial results gracefully (3 of 5 agents complete, 2 still waiting due to rate limiting).

8. **Model fallback.** If Gemini is down, should the Innovation Council fall back to all-Claude? Or refuse to run? The spec argues multi-model diversity is structural — falling back to single-model defeats the purpose. But availability matters. Probably: warn the user and let them choose.

### Design

9. **The blank canvas problem.** Custom councils are powerful but intimidating. Most users won't know which agents to pick. The AI-suggested composition needs to be excellent, or custom councils will be unused. Consider a "guided composition" flow: "Tell me about your question" → "Here's what I'd suggest" → "Tweak if you want."

10. **Information density.** A 5-agent parallel council produces ~2,500 words of agent output plus a synthesis. A 2-phase Innovation Council produces ~5,000+ words. How much does the user actually read? Consider: collapsed-by-default agent cards with a "key claim" visible, expandable for full text. The synthesis is always expanded.

11. **The "was that worth it?" signal.** After a session, the user should be able to give lightweight feedback (👍/👎, or a 1-5 quality rating). Over time, this reveals which council configurations and which agents produce the most valued output. This data is gold for improving prompt design and suggesting better compositions.

---

*This spec is the foundation. Build Phase 1, ship it, learn from usage, iterate. The mixing and chaining capabilities (Phase 4) are where the product becomes genuinely novel — but they require the three canonical councils to work well first. Don't skip ahead.*

*End of spec.*
