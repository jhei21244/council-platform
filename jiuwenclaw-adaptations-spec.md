# JiuwenClaw Adaptations — Implementation Spec

**Date:** 2026-03-29  
**Status:** Draft — ready for J's review  
**Source:** https://github.com/openJiuwen-ai/jiuwenclaw  
**Context:** Three patterns from JiuwenClaw that solve real problems we have. Ordered by impact.

---

## 1. Context Offloading (Pre-Compaction Hook)

### The Problem

When OpenClaw compacts context, tool outputs are removed with `[compacted: tool output removed to free context]` markers. This is **destructive** — the data is gone. Decisions made during tool-heavy work (data analysis, code review, multi-step builds) vanish if they weren't explicitly written to a file before compaction hit.

Our current mitigation is the "Write-on-Decide" rule in AGENTS.md — but that depends on the agent remembering to write, which is exactly the thing that fails under context pressure.

### JiuwenClaw's Approach

They use `[[OFFLOAD:...]]` markers. Before compaction, bulky content is:
1. Summarised into a compact form
2. Indexed for retrieval
3. Replaced in context with a marker that points to the stored version

When the context needs that information again, it can be pulled back from storage.

Their trigger: when message count exceeds `messages_threshold` (e.g. 3) or total tokens exceed `tokens_threshold` (default 20,000). Large messages (>1,000 tokens) are prioritised for offload. Recent turns are protected (`messages_to_keep`).

### Our Implementation

#### Architecture

```
Session context grows
        │
        ▼
┌──────────────────────────┐
│  Offload Trigger Check   │  ← every N messages or token threshold
│  (pre-compaction hook)   │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  Classify each message   │
│  - tool output (large)   │  ← priority offload
│  - agent reasoning       │  ← summarise
│  - user messages         │  ← preserve
│  - decisions/actions     │  ← extract & persist
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  For each offload target:│
│  1. Summarise (LLM call) │
│  2. Write full version   │
│     to session store     │
│  3. Replace in context   │
│     with summary +       │
│     [[OFFLOAD:id]] tag   │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  Decision Extractor      │  ← scan for decisions, conclusions,
│  (runs before offload)   │     action items in content about
│                          │     to be compressed
│  Writes to:              │
│  - memory/YYYY-MM-DD.md  │
│  - NOW.md if relevant    │
└──────────────────────────┘
```

#### Storage

```
workspace/session-offload/
├── {session_id}/
│   ├── offload_001.md      # Full content of first offloaded block
│   ├── offload_002.md      # ...
│   └── manifest.json       # Index: id → summary, timestamp, source_role, token_count
```

#### Manifest Format

```json
{
  "session_id": "abc-123",
  "offloads": [
    {
      "id": "offload_001",
      "timestamp": "2026-03-29T15:30:00Z",
      "source_role": "tool",
      "tool_name": "exec",
      "summary": "Ran greyhound model evaluation: 19.6% win rate, -19.3% ROI after leakage correction. Key finding: original 57% win rate was due to data leakage in temporal split.",
      "token_count_original": 3847,
      "token_count_summary": 89,
      "file": "offload_001.md"
    }
  ]
}
```

#### Context Replacement

Before:
```
[tool result: exec — 3,847 tokens of model evaluation output]
```

After offload:
```
[[OFFLOAD:offload_001]] Greyhound model eval: 19.6% win rate, -19.3% ROI post-leakage correction. 57% headline was data leakage. Full output stored. Use memory_get or read to retrieve if needed.
```

#### Decision Extraction (the key innovation over JiuwenClaw)

JiuwenClaw just summarises and stores. We go further: before offloading, scan the content for **decisions, conclusions, and action items** and persist those to memory files automatically.

```python
DECISION_PATTERNS = [
    r"(?:decided|decision|confirmed|agreed|conclusion|verdict|finding)[:\s]",
    r"(?:going forward|from now on|the plan is|we'll|action item)",
    r"(?:J said|J confirmed|J wants|J approved)",
    r"(?:changed to|switched to|updated to|now using)",
]
```

Extracted decisions get written to the daily note under `## Auto-Extracted (Pre-Offload)` so they survive even if the session dies.

#### Implementation Path

**Option A: OpenClaw Plugin/Hook (ideal)**
- Feature request: `agents.defaults.context.preCompactionHook` — a script that runs before compaction
- OpenClaw calls our script with the messages about to be compacted
- We summarise, store, and return the replacement markers
- **Requires OpenClaw change** — submit as feature request

**Option B: Agent-Side Proactive (works now)**
- Periodic self-check during long sessions: "Am I approaching context limits?"
- When estimated tokens > threshold, proactively summarise and offload old tool outputs
- Write summaries to files, update context references
- **Limitation:** Agent can't modify its own context window, only write files
- **But:** The act of writing decisions to files before compaction hits is the real value

**Option C: Cron-Based Session Monitor (hybrid)**
- A lightweight daemon watches session token counts via OpenClaw API
- When approaching limits, triggers a sub-agent to:
  1. Read the session's recent tool outputs
  2. Extract decisions and write to daily notes
  3. Create offload summaries
- **Advantage:** Runs independently of the main agent's context awareness

**Recommendation:** Start with **Option B** (agent-side) — add a periodic context health check to AGENTS.md instructions. Simultaneously submit **Option A** as an OpenClaw feature request.

#### Config

```yaml
# Proposed for AGENTS.md or openclaw.json
context_offload:
  enabled: true
  token_threshold: 80000        # trigger when estimated tokens exceed this
  large_message_threshold: 1500 # messages above this token count get offloaded first
  messages_to_keep: 4           # always keep last N user/assistant turns
  offload_roles: ["tool"]       # which roles to target (tool outputs first)
  extract_decisions: true       # run decision extractor before offload
  storage_dir: "workspace/session-offload"
```

---

## 2. Skill Self-Evolution

### The Problem

When a skill's tool call fails, or J says "that's wrong", the correction lives only in the conversation. Next session, the same mistake happens again. Our `self-improving-agent` skill captures some learnings, but it's manual — the agent has to decide to invoke it. Most failures silently repeat.

### JiuwenClaw's Approach

A `SignalDetector` watches for:
- **Execution failures:** error, exception, timeout, permission denied, connection refused, command not found
- **User corrections:** "that's wrong", "should be", "actually", "not that", "no—"

Detected signals create structured records in `evolutions.json` next to the skill's `SKILL.md`. On next skill load, pending evolutions are merged into the skill doc — adding troubleshooting entries for failures, examples for corrections.

### Our Implementation

#### Signal Detection

Add to every agent's base instructions (AGENTS.md):

```markdown
## Skill Evolution (Auto)

After any tool/skill failure or user correction:
1. Identify which skill was active
2. Classify the signal:
   - `execution_failure` — tool returned error, timeout, unexpected result
   - `user_correction` — J said "wrong", "should be", "actually", "not that"
   - `missing_capability` — J asked for something the skill can't do
3. Write an evolution record to `{skill_dir}/evolutions.json`
4. On next use of that skill, check for pending evolutions and apply
```

#### Evolution Record Format

```json
{
  "skill_id": "tab-collector",
  "version": "1.0.0",
  "entries": [
    {
      "id": "ev_20260329_001",
      "source": "execution_failure",
      "timestamp": "2026-03-29T15:00:00Z",
      "context": "curl_cffi raised SSLError when TAB API returned 403 — CloudFlare challenge page instead of JSON",
      "change": {
        "section": "Troubleshooting",
        "action": "append",
        "content": "- On 403/SSLError: TAB API is returning CloudFlare challenge. Wait 5 minutes and retry. If persistent, the impersonation target may need updating (check Chrome version in curl_cffi config)."
      },
      "applied": false,
      "agent": "clio"
    },
    {
      "id": "ev_20260329_002",
      "source": "user_correction",
      "timestamp": "2026-03-29T16:00:00Z",
      "context": "J said 'no the API only serves today's data, not yesterday' — agent assumed historical data was available",
      "change": {
        "section": "Key Constraints",
        "action": "append",
        "content": "- TAB API only serves **today's** data. Historical data is permanently gone if not collected on the day. Never assume yesterday's data is available via the API."
      },
      "applied": false,
      "agent": "clio"
    }
  ]
}
```

#### Evolution Application

When a skill is loaded (agent reads SKILL.md):

```python
# Pseudocode for skill loading
def load_skill(skill_dir):
    skill_md = read(f"{skill_dir}/SKILL.md")
    evolutions_file = f"{skill_dir}/evolutions.json"
    
    if exists(evolutions_file):
        evolutions = json.load(evolutions_file)
        pending = [e for e in evolutions["entries"] if not e["applied"]]
        
        if pending:
            for entry in pending:
                # Merge into SKILL.md at the appropriate section
                skill_md = apply_evolution(skill_md, entry)
                entry["applied"] = True
                entry["applied_at"] = now()
            
            write(f"{skill_dir}/SKILL.md", skill_md)
            json.dump(evolutions, evolutions_file)
    
    return skill_md
```

#### Solidification

Pending evolutions accumulate in `evolutions.json`. Periodically (or via `/evolve` command equivalent), they're merged into SKILL.md itself:

- **Execution failures** → appended to `## Troubleshooting` section
- **User corrections** → appended to `## Examples` or `## Key Constraints`
- **Missing capabilities** → appended to `## Limitations` or flagged as enhancement

#### What Changes

| File | Change |
|---|---|
| `AGENTS.md` | Add Skill Evolution section to agent instructions |
| `skills/self-improving-agent/SKILL.md` | Update to use evolutions.json pattern instead of ad-hoc learnings |
| Each skill dir | Gets `evolutions.json` created on first detected signal |
| New script: `scripts/apply_evolutions.py` | Batch-apply pending evolutions across all skills |

#### Scope Guard

- Evolutions only append — they never delete or rewrite existing SKILL.md content
- Each evolution is <200 tokens to avoid bloating the skill
- Max 20 pending evolutions per skill; oldest auto-solidify after that
- Agent attribution tracks which agent contributed each evolution (useful in multi-agent setup)

---

## 3. Hybrid Memory Search (BM25 + Vector)

### The Problem

Our current `memory_search` uses Gemini embeddings only. Semantic search is great for fuzzy intent ("what did we decide about deployment?") but misses exact keyword matches. If J says "find the entry about ArbiTrack", semantic search might return vaguely related entries about arbitrage while missing the one that literally says "ArbiTrack".

### JiuwenClaw's Approach

Combined score: `score = vectorWeight × vectorScore + textWeight × textScore`  
Defaults: vector 0.7, text 0.3.

Storage: SQLite with `chunks_fts` (FTS5 for BM25) + `chunks_vec` (vec0 for embeddings).

### Our Implementation

#### Architecture

```
memory_search("ArbiTrack deployment")
        │
        ├──► Vector search (Gemini embeddings) ──► scored results
        │
        ├──► BM25 search (SQLite FTS5) ──► scored results  
        │
        └──► Merge: 0.7 × vector + 0.3 × text ──► final ranked results
```

#### SQLite FTS5 Index

```sql
-- New table alongside existing memory search
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    path,           -- file path
    line_start,     -- start line
    line_end,       -- end line  
    content,        -- text chunk
    tokenize='porter unicode61'  -- stemming + unicode support
);
```

#### Index Building

```python
# scripts/memory/build_fts_index.py
import sqlite3
import os
import re

DB_PATH = "workspace/memory_search.db"
MEMORY_DIR = "workspace/memory"
CHUNK_SIZE = 8  # lines per chunk, matching vector chunk size

def build_index():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS memory_fts")
    conn.execute("""
        CREATE VIRTUAL TABLE memory_fts USING fts5(
            path, line_start, line_end, content,
            tokenize='porter unicode61'
        )
    """)
    
    for root, dirs, files in os.walk(MEMORY_DIR):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, "workspace")
            
            with open(fpath) as f:
                lines = f.readlines()
            
            for i in range(0, len(lines), CHUNK_SIZE):
                chunk_lines = lines[i:i+CHUNK_SIZE]
                content = "".join(chunk_lines).strip()
                if content:
                    conn.execute(
                        "INSERT INTO memory_fts VALUES (?, ?, ?, ?)",
                        (rel_path, i+1, min(i+CHUNK_SIZE, len(lines)), content)
                    )
    
    conn.commit()
    conn.close()
```

#### Hybrid Search

```python
# scripts/memory/hybrid_search.py
def hybrid_search(query, vector_weight=0.7, text_weight=0.3, max_results=10):
    # 1. Vector search (existing Gemini embeddings)
    vector_results = existing_memory_search(query, max_results=max_results*2)
    
    # 2. BM25 search
    conn = sqlite3.connect(DB_PATH)
    bm25_results = conn.execute("""
        SELECT path, line_start, line_end, content, 
               bm25(memory_fts) as score
        FROM memory_fts 
        WHERE memory_fts MATCH ?
        ORDER BY score
        LIMIT ?
    """, (fts5_query(query), max_results*2)).fetchall()
    conn.close()
    
    # 3. Merge with weighted scores
    merged = {}
    
    for r in vector_results:
        key = f"{r['path']}:{r['startLine']}"
        merged[key] = {
            **r,
            "vector_score": r["score"],
            "text_score": 0,
        }
    
    for path, start, end, content, score in bm25_results:
        key = f"{path}:{start}"
        if key in merged:
            merged[key]["text_score"] = normalize_bm25(score)
        else:
            merged[key] = {
                "path": path,
                "startLine": start,
                "endLine": end,
                "snippet": content[:200],
                "vector_score": 0,
                "text_score": normalize_bm25(score),
            }
    
    # Combined score
    for r in merged.values():
        r["combined_score"] = (
            vector_weight * r["vector_score"] + 
            text_weight * r["text_score"]
        )
    
    return sorted(merged.values(), key=lambda x: -x["combined_score"])[:max_results]
```

#### Integration

We can't modify OpenClaw's `memory_search` tool directly. Options:

**Option A: Wrapper script**
- Build `scripts/memory/hybrid_search.py` as a standalone tool
- Agent calls it via `exec` when semantic search alone isn't finding the right result
- Low integration, high flexibility

**Option B: FTS as fallback**
- Agent tries `memory_search` first
- If results are low-confidence (score < 0.5), additionally runs FTS5 search
- Merges results manually

**Option C: Build into heartbeat memory system**
- `heartbeat_memory.py` already manages the memory architecture
- Add FTS5 index building to the heartbeat cycle
- Expose `hybrid_search` as a function in the memory scripts
- Agent calls it from daily priming

**Recommendation:** Option C — integrate into existing memory architecture. The FTS5 index rebuilds quickly (<1s for our memory volume) and can run every heartbeat.

#### Index Maintenance

- Rebuild on heartbeat (every 4-6 hours) — fast enough for our volume
- Watchdog optional (JiuwenClaw uses one) — overkill for us given heartbeat frequency
- Memory files change slowly; full rebuild is fine vs incremental

---

## Implementation Priority

| # | Feature | Impact | Effort | Dependencies |
|---|---|---|---|---|
| 1 | **Context Offloading (Option B)** | HIGH — directly addresses our #1 pain point | MEDIUM — agent instructions + decision extractor script | None |
| 2 | **Skill Self-Evolution** | MEDIUM — prevents repeat failures | LOW — evolutions.json + AGENTS.md update | None |
| 3 | **Hybrid Memory Search** | MEDIUM — better recall for exact terms | LOW — SQLite FTS5 script + integration | None |

**Recommended order:** 2 → 3 → 1  
(Skill evolution is lowest effort and immediately useful. Hybrid search is a quick win. Context offloading is highest impact but needs the most thought about the right integration point.)

---

## Open Questions

1. **Context offloading without OpenClaw hook:** Can the agent reliably detect it's approaching context limits? We don't have a `token_count` API. Heuristic: count messages in visible history?

2. **Evolution conflicts in multi-agent:** If Clio and Bandage both evolve the same skill, how do we merge? Proposal: agent attribution + timestamp ordering, latest wins for conflicting sections.

3. **FTS5 query syntax:** BM25 needs query terms, not natural language. Do we strip stop words and pass keywords, or use the FTS5 query parser directly?

4. **Evolution quality control:** JiuwenClaw uses LLM to generate evolution records. Should we do the same (costs tokens) or use templates (cheaper, less flexible)?

---

*End of spec. Built from analysis of JiuwenClaw v0.1.7 (Apache 2.0 licensed). All implementations are independent — no code copied.*
