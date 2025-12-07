#!/usr/bin/env python3
"""
Export decisions and audit log from demo.db into artifacts/ directory.

Usage: python scripts/export_history.py
"""
import sqlite3
import csv
import json
import os
from pathlib import Path

DB = Path('demo.db')
OUT = Path('artifacts')


def export_decisions(conn, out_dir: Path):
    cur = conn.cursor()
    cur.execute("SELECT id,invoice_id,decision,reviewer_id,created_at,updated_at FROM checkpoints WHERE decision IS NOT NULL ORDER BY created_at DESC")
    rows = cur.fetchall()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / 'decisions.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['checkpoint_id','invoice_id','decision','reviewer_id','created_at_unix','updated_at_unix'])
        for r in rows:
            w.writerow(r)
    return csv_path


def export_audit(conn, out_dir: Path):
    cur = conn.cursor()
    cur.execute('SELECT id,invoice_id,stage,message,ts FROM audit_log ORDER BY ts ASC')
    rows = cur.fetchall()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / 'audit_log.json'
    # serialize rows into list of dicts
    entries = []
    for r in rows:
        entries.append({'id': r[0], 'invoice_id': r[1], 'stage': r[2], 'message': r[3], 'ts': r[4]})
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2)
    return json_path


def main():
    if not DB.exists():
        print('demo.db not found; nothing to export')
        return 1
    conn = sqlite3.connect(str(DB))
    try:
        dpath = export_decisions(conn, OUT)
        jpath = export_audit(conn, OUT)
        print('Exported:', dpath, jpath)
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
