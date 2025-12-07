import sqlite3
import json
import time
import csv
import os
import sys
import subprocess
from typing import Optional

DB_PATH = "./demo.db"

CREATE_CHECKPOINT_SQL = """
CREATE TABLE IF NOT EXISTS checkpoints (
  id TEXT PRIMARY KEY,
  invoice_id TEXT,
  state_blob TEXT,
  status TEXT,
  created_at REAL,
  updated_at REAL,
  reviewer_id TEXT,
  decision TEXT
)
"""

CREATE_AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id TEXT,
  stage TEXT,
  message TEXT,
  ts REAL
)
"""


def init_db(db_path: Optional[str] = None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(CREATE_CHECKPOINT_SQL)
    cur.execute(CREATE_AUDIT_SQL)
    conn.commit()
    return conn


def save_checkpoint(conn, checkpoint_id: str, invoice_id: str, state: dict):
    now = time.time()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO checkpoints (id, invoice_id, state_blob, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (checkpoint_id, invoice_id, json.dumps(state), 'PAUSED', now, now),
    )
    conn.commit()


def list_pending(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, invoice_id, state_blob, created_at FROM checkpoints WHERE status='PAUSED'")
    rows = cur.fetchall()
    result = []
    for r in rows:
        result.append({
            'checkpoint_id': r[0],
            'invoice_id': r[1],
            'state': json.loads(r[2]),
            'created_at': r[3]
        })
    return result


def save_decision(conn, checkpoint_id: str, reviewer_id: str, decision: str):
    now = time.time()
    cur = conn.cursor()
    cur.execute(
        "UPDATE checkpoints SET reviewer_id=?, decision=?, status=?, updated_at=? WHERE id=?",
        (reviewer_id, decision, 'DECIDED', now, checkpoint_id),
    )
    conn.commit()
    # Append decision to a local CSV file for easy auditing/streaming
    try:
        # Fetch invoice_id and timestamps for this checkpoint
        cur.execute("SELECT invoice_id, created_at, updated_at FROM checkpoints WHERE id=?", (checkpoint_id,))
        row = cur.fetchone()
        invoice_id = row[0] if row else ''
        created_at = row[1] if row else None
        updated_at = row[2] if row else now

        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        csv_path = os.path.join(logs_dir, 'decisions.csv')
        write_header = not os.path.exists(csv_path)
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['checkpoint_id', 'invoice_id', 'decision', 'reviewer_id', 'created_at_unix', 'updated_at_unix'])
            writer.writerow([checkpoint_id, invoice_id, decision, reviewer_id, created_at, updated_at])
    except Exception:
        # Non-fatal: do not raise errors from logging/CSV writes
        pass
    # Trigger an async export of history to artifacts/ for external consumption.
    try:
        script_path = os.path.join(os.getcwd(), 'scripts', 'export_history.py')
        if os.path.exists(script_path):
            # Fire-and-forget: run exporter in background to avoid blocking runner.
            if sys.platform == 'win32':
                # On Windows, hide the console window
                subprocess.Popen([sys.executable, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
            else:
                subprocess.Popen([sys.executable, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def fetch_checkpoint(conn, checkpoint_id: str):
    cur = conn.cursor()
    cur.execute("SELECT id, invoice_id, state_blob, status FROM checkpoints WHERE id=?", (checkpoint_id,))
    r = cur.fetchone()
    if not r:
        return None
    return { 'id': r[0], 'invoice_id': r[1], 'state': json.loads(r[2]), 'status': r[3] }


def mark_completed(conn, checkpoint_id: str):
    now = time.time()
    cur = conn.cursor()
    cur.execute("UPDATE checkpoints SET status=? , updated_at=? WHERE id=?", ('COMPLETED', now, checkpoint_id))
    conn.commit()


def append_audit(conn, invoice_id: str, stage: str, message: str):
    now = time.time()
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log (invoice_id, stage, message, ts) VALUES (?,?,?,?)", (invoice_id, stage, message, now))
    conn.commit()
