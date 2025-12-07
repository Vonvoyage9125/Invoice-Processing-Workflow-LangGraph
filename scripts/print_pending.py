import sqlite3

conn = sqlite3.connect('demo.db')
cur = conn.cursor()
cur.execute("SELECT id, invoice_id, status, decision, reviewer_id FROM checkpoints")
rows = cur.fetchall()
if not rows:
    print('No checkpoints found')
else:
    for r in rows:
        print('id:', r[0], 'invoice:', r[1], 'status:', r[2], 'decision:', r[3], 'reviewer:', r[4])
