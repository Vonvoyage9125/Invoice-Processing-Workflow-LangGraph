import sqlite3
import sys
import os

# Ensure project root is on sys.path so `from src import db` works
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src import db

if len(sys.argv) < 3:
    print('Usage: post_decision.py <checkpoint_id> <ACCEPT|REJECT> [reviewer_id]')
    sys.exit(2)
cp = sys.argv[1]
dec = sys.argv[2]
rev = sys.argv[3] if len(sys.argv) > 3 else 'script_user'

conn = db.init_db()
db.save_decision(conn, cp, rev, dec)
# mark completed as API does
db.mark_completed(conn, cp)
print('Decision saved for', cp, dec, rev)
