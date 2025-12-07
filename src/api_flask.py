from flask import Flask, jsonify, request, send_from_directory
from src import db
import os

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))


@app.route('/human-review/pending', methods=['GET'])
def list_pending():
    conn = db.init_db()
    items = db.list_pending(conn)
    # Trim state for response
    resp_items = []
    for it in items:
        resp_items.append({
            'checkpoint_id': it['checkpoint_id'],
            'invoice_id': it['invoice_id'],
            'created_at': it['created_at'],
            'summary': {
                'vendor_name': it['state'].get('invoice', {}).get('vendor_name'),
                'amount': it['state'].get('invoice', {}).get('amount')
            }
        })
    return jsonify({'items': resp_items})


@app.route('/human-review/decision', methods=['POST'])
def post_decision():
    payload = request.get_json(force=True)
    checkpoint_id = payload.get('checkpoint_id')
    decision = payload.get('decision')
    reviewer_id = payload.get('reviewer_id', 'web_user')
    if not checkpoint_id or not decision:
        return jsonify({'error': 'checkpoint_id and decision required'}), 400
    conn = db.init_db()
    db.save_decision(conn, checkpoint_id, reviewer_id, decision)
    db.mark_completed(conn, checkpoint_id)
    return jsonify({'resume_token': checkpoint_id, 'next_stage': 'RECONCILE'})


@app.route('/human-review/ui', methods=['GET'])
def ui():
    # Serve a minimal UI page
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'ui.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=False)
