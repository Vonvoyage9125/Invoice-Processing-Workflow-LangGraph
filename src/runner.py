import sys
import json
import time
import uuid
import os
from src import db
from src import nodes

WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), '..', 'workflow.json')

NODE_MAP = {
    'IngestNode': nodes.IngestNode,
    'OcrNlpNode': nodes.OcrNlpNode,
    'NormalizeEnrichNode': nodes.NormalizeEnrichNode,
    'ErpFetchNode': nodes.ErpFetchNode,
    'TwoWayMatcherNode': nodes.TwoWayMatcherNode,
    'CheckpointNode': nodes.CheckpointNode,
    'HumanReviewNode': nodes.HumanReviewNode,
    'ReconciliationNode': nodes.ReconciliationNode,
    'ApprovalNode': nodes.ApprovalNode,
    'PostingNode': nodes.PostingNode,
    'NotifyNode': nodes.NotifyNode,
    'CompleteNode': nodes.CompleteNode,
}


def load_workflow():
    with open(WORKFLOW_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_workflow(invoice_obj, db_path=None, auto_decide=True, decision_delay=2):
    wf = load_workflow()
    config = wf.get('config', {})
    conn = db.init_db(db_path)
    state = { 'invoice': invoice_obj }
    # Simple sequential runner
    for stage in wf['stages']:
        stage_id = stage['id']
        agent_name = stage['agent']
        AgentCls = NODE_MAP.get(agent_name)
        if not AgentCls:
            print(f"No agent found for {agent_name}, skipping")
            continue
        agent = AgentCls(conn, config)
        print(f"==> Running stage {stage_id} ({agent_name})")
        state = agent.run(state)
        # If checkpointed and paused, break and wait for decision
        if state.get('paused'):
            checkpoint_id = state.get('checkpoint_id')
            print(f"Workflow paused at checkpoint {checkpoint_id}")
            # In a production scenario we'd notify human review queue and return.
            # For demo, either poll DB or auto-resolve after delay.
            if auto_decide:
                print(f"Auto-decision will be applied in {decision_delay}s (ACCEPT)")
                time.sleep(decision_delay)
                db.save_decision(conn, checkpoint_id, 'demo_reviewer', 'ACCEPT')
                print("Decision saved: ACCEPT")
                db.mark_completed(conn, checkpoint_id)
                # continue processing: assume ACCEPT -> next stage is RECONCILE
                state.pop('paused', None)
                continue
            else:
                print("Waiting for human decision (external)")
                # poll until decision exists (accept DECIDED or COMPLETED statuses)
                while True:
                    pending = db.fetch_checkpoint(conn, checkpoint_id)
                    if pending and pending.get('status') in ('DECIDED', 'COMPLETED'):
                        decision = pending.get('decision')
                        print(f'Decision observed: {decision}; resuming')
                        # Handle REJECT case: finalize workflow and stop
                        if decision and decision.upper() == 'REJECT':
                            print('Human rejected the invoice. Finalizing with status REQUIRES_MANUAL_HANDLING')
                            # create final payload and exit
                            state['final_payload'] = { 'invoice_id': state['invoice']['invoice_id'], 'status': 'REQUIRES_MANUAL_HANDLING' }
                            # append audit
                            db.append_audit(conn, state['invoice']['invoice_id'], 'HITL_DECISION', f'Rejected by reviewer {pending.get("reviewer_id")}')
                            return state
                        break
                    time.sleep(1)
                state.pop('paused', None)
                continue
    print('Workflow finished. Final payload:')
    print(json.dumps(state.get('final_payload', {}), indent=2))
    return state


if __name__ == '__main__':
    # Simple CLI: python -m src.runner <invoice.json> [--no-auto]
    if len(sys.argv) < 2:
        print('Usage: python -m src.runner <invoice.json> [--no-auto]')
        sys.exit(2)
    invoice_path = sys.argv[1]
    auto_decide = True
    if '--no-auto' in sys.argv or '--manual' in sys.argv:
        auto_decide = False
    with open(invoice_path, 'r', encoding='utf-8') as f:
        inv = json.load(f)
    run_workflow(inv, auto_decide=auto_decide)
