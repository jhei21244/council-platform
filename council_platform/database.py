"""Database setup and connection management using aiosqlite."""

import aiosqlite
import os
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).parent.parent / "council.db"))

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS agents (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    cognitive_function TEXT,
    home_council TEXT,
    icon        TEXT,
    default_model TEXT DEFAULT 'claude',
    tags        TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS council_templates (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    agent_ids   TEXT NOT NULL,
    mode        TEXT NOT NULL,
    phase_config TEXT,
    description TEXT,
    icon        TEXT,
    accent_color TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    council_template_id TEXT,
    council_type TEXT NOT NULL,
    title       TEXT,
    input_text  TEXT NOT NULL,
    input_meta  TEXT,
    status      TEXT DEFAULT 'active',
    chain_parent_id TEXT,
    chain_position INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (council_template_id) REFERENCES council_templates(id),
    FOREIGN KEY (chain_parent_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS session_agents (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    phase       INTEGER DEFAULT 1,
    model_used  TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS deliberation_turns (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    phase       INTEGER DEFAULT 1,
    turn_order  INTEGER,
    content     TEXT NOT NULL,
    confidence  REAL,
    model_used  TEXT,
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    cost_usd    REAL,
    started_at  TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS syntheses (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    content     TEXT NOT NULL,
    synthesis_type TEXT,
    model_used  TEXT,
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    cost_usd    REAL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(council_type);
CREATE INDEX IF NOT EXISTS idx_sessions_chain ON sessions(chain_parent_id);
CREATE INDEX IF NOT EXISTS idx_turns_session ON deliberation_turns(session_id);
CREATE INDEX IF NOT EXISTS idx_turns_phase ON deliberation_turns(session_id, phase);
"""


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()
