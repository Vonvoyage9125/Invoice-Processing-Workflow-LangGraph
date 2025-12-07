import uuid
from src import db
from src.bigtool import BigtoolPicker
from src.mcp_clients import CommonClient, AtlasClient, compute_match_score


class BaseNode:
    def __init__(self, conn, config):
        self.conn = conn
        self.config = config
        self.common = CommonClient()
        self.atlas = AtlasClient()
        self.bigtool = BigtoolPicker()

    def log(self, invoice_id, stage, message):
        db.append_audit(self.conn, invoice_id, stage, message)


class IngestNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        inv['raw_id'] = str(uuid.uuid4())
        self.log(inv['invoice_id'], 'INTAKE', f"Persisted raw_id {inv['raw_id']}")
        return state


class OcrNlpNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        pick = self.bigtool.select('ocr')
        self.log(inv['invoice_id'], 'UNDERSTAND', f"Bigtool selected: {pick}")
        text = self.atlas.ocr(inv.get('attachments', [None])[0])
        items = self.common.parse_line_items(text)
        state['parsed_invoice'] = { 'invoice_text': text, 'parsed_line_items': items }
        self.log(inv['invoice_id'], 'UNDERSTAND', 'Parsed line items')
        return state


class NormalizeEnrichNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        norm = self.common.normalize_vendor(inv.get('vendor_name',''))
        pick = self.bigtool.select('enrichment')
        self.log(inv['invoice_id'], 'PREPARE', f"Bigtool selected for enrichment: {pick}")
        enrich = self.atlas.enrich_vendor(inv.get('vendor_name',''))
        state['vendor_profile'] = { **norm, **enrich }
        state['normalized_invoice'] = { 'amount': inv.get('amount'), 'currency': inv.get('currency'), 'line_items': state.get('parsed_invoice',{}).get('parsed_line_items',[]) }
        state['flags'] = self.common.compute_flags(state['normalized_invoice'])
        self.log(inv['invoice_id'], 'PREPARE', 'Vendor normalized and enriched')
        return state


class ErpFetchNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        pick = self.bigtool.select('erp_connector')
        self.log(inv['invoice_id'], 'RETRIEVE', f"ERP tool picked: {pick}")
        pos = self.atlas.fetch_pos(inv.get('vendor_name',''))
        state['matched_pos'] = pos
        self.log(inv['invoice_id'], 'RETRIEVE', f"Fetched {len(pos)} PO(s)")
        return state


class TwoWayMatcherNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        pos = state.get('matched_pos', [])
        score = compute_match_score(inv, pos)
        state['match_score'] = score
        threshold = self.config.get('match_threshold', 0.9)
        state['match_result'] = 'MATCHED' if score >= threshold else 'FAILED'
        self.log(inv['invoice_id'], 'MATCH_TWO_WAY', f"Match score {score}, result {state['match_result']}")
        return state


class CheckpointNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        checkpoint_id = str(uuid.uuid4())
        db.save_checkpoint(self.conn, checkpoint_id, inv['invoice_id'], state)
        self.log(inv['invoice_id'], 'CHECKPOINT_HITL', f"Checkpoint created {checkpoint_id}")
        state['checkpoint_id'] = checkpoint_id
        # Indicate paused state by returning a special key
        state['paused'] = True
        return state


class HumanReviewNode(BaseNode):
    def run(self, state: dict):
        # For demo, decision is read from DB (this node not used in runner since runner polls)
        return state


class ReconciliationNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        entries = self.common.build_accounting_entries(inv)
        state['accounting_entries'] = entries
        self.log(inv['invoice_id'], 'RECONCILE', 'Accounting entries built')
        return state


class ApprovalNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        amt = inv.get('amount', 0)
        if amt < 10000:
            state['approval_status'] = 'AUTO_APPROVED'
        else:
            state['approval_status'] = 'ESCALATED'
        self.log(inv['invoice_id'], 'APPROVE', f"Approval status {state['approval_status']}")
        return state


class PostingNode(BaseNode):
    def run(self, state: dict):
        entries = state.get('accounting_entries', [])
        resp = self.atlas.post_to_erp(entries)
        state['posted'] = resp
        self.log(state['invoice']['invoice_id'], 'POSTING', f"Posted to ERP: {resp}")
        return state


class NotifyNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        resp = self.atlas.notify(['vendor','finance'], 'Invoice processed')
        state['notify_status'] = resp
        self.log(inv['invoice_id'], 'NOTIFY', 'Notifications sent')
        return state


class CompleteNode(BaseNode):
    def run(self, state: dict):
        inv = state['invoice']
        state['final_payload'] = { 'invoice_id': inv['invoice_id'], 'status': 'COMPLETED' }
        self.log(inv['invoice_id'], 'COMPLETE', 'Workflow complete')
        return state
