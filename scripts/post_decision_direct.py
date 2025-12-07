import sqlite3, time, sys

if len(sys.argv) < 3:
    print('Usage: post_decision_direct.py <checkpoint_id> <ACCEPT|REJECT> [reviewer_id]')
    sys.exit(2)
cp = sys.argv[1]
dec = sys.argv[2]
rev = sys.argv[3] if len(sys.argv) > 3 else 'script_user'

conn = sqlite3.connect('demo.db')
cur = conn.cursor()
now = time.time()
cur.execute("UPDATE checkpoints SET reviewer_id=?, decision=?, status=?, updated_at=? WHERE id=?", (rev, dec, 'DECIDED', now, cp))
conn.commit()
# Also set COMPLETED to simulate API mark_completed
cur.execute("UPDATE checkpoints SET status=?, updated_at=? WHERE id=?", ('COMPLETED', now, cp))
conn.commit()
print('Posted decision', dec, 'for', cp, 'by', rev)
