#!/usr/bin/env python3
import sqlite3
import sys

DB='demo.db'
try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='audit_log'")
    exists=cur.fetchone()[0]
    print('TABLE_EXISTS', exists)
    if not exists:
        print('No audit_log table found.')
        sys.exit(0)
    cur.execute('SELECT COUNT(*) FROM audit_log')
    before=cur.fetchone()[0]
    print('COUNT_BEFORE_DELETE', before)
    cur.execute('DELETE FROM audit_log')
    conn.commit()
    cur.execute('VACUUM')
    conn.commit()
    cur.execute('SELECT COUNT(*) FROM audit_log')
    after=cur.fetchone()[0]
    print('COUNT_AFTER_DELETE', after)
    conn.close()
except Exception as e:
    print('ERROR', e)
    sys.exit(2)
