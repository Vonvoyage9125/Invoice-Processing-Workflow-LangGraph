import time
from src.bigtool import BigtoolPicker
from src.adapters import get_adapter


class CommonClient:
    def __init__(self):
        self.bigtool = BigtoolPicker()

    def ocr(self, attachment_path: str):
        # stub: return text
        return "Extracted invoice text (mock)"

    def parse_line_items(self, text: str):
        # If a semantic NLP tool is available in the bigtool pools, prefer it
        try:
            pick = self.bigtool.select('nlp')
            if pick == 'anthropic':
                adapter = get_adapter('anthropic', {})
                # Use a TASK header that AnthropicAdapter recognizes for richer behavior
                parsed = adapter.call_model(prompt=f"TASK:PARSE_INVOICE\n{text}")
                return parsed.get('parsed_line_items', [ { 'desc': 'Widgets', 'qty': 10, 'unit_price': 1234.5, 'total': 12345.0 } ])
        except Exception:
            # Fallback to mock
            pass
        return [ { 'desc': 'Widgets', 'qty': 10, 'unit_price': 1234.5, 'total': 12345.0 } ]

    def normalize_vendor(self, vendor_name: str):
        return { 'normalized_name': vendor_name.strip().title(), 'tax_id': None }

    def compute_flags(self, invoice):
        return { 'missing_info': [], 'risk_score': 0.1 }

    def build_accounting_entries(self, invoice):
        return [ { 'account': 'AP', 'debit': invoice.get('amount',0), 'credit': 0 } ]


class AtlasClient:
    def __init__(self):
        self.bigtool = BigtoolPicker()

    def ocr(self, attachment_path: str):
        # Prefer an NLP provider if configured for semantic OCR/parse
        try:
            pick = self.bigtool.select('nlp')
            if pick == 'anthropic':
                adapter = get_adapter('anthropic', {})
                parsed = adapter.call_model(prompt=f"TASK:OCR\nPlease extract the invoice text from attachment: {attachment_path}")
                return parsed.get('invoice_text') or parsed.get('parsed_line_items') or "OCR via ATLAS (mock)"
        except Exception:
            pass
        return "OCR via ATLAS (mock)"

    def enrich_vendor(self, vendor_name: str):
        try:
            # Some setups may route enrichment to an LLM-based enrichment via 'nlp'
            pick = self.bigtool.select('nlp')
            if pick == 'anthropic':
                adapter = get_adapter('anthropic', {})
                parsed = adapter.call_model(prompt=f"TASK:ENRICH_VENDOR\nPlease return JSON with tax_id and credit_score for vendor: {vendor_name}")
                # Map parsed output to expected enrichment keys conservatively
                if isinstance(parsed, dict):
                    return {
                        'tax_id': parsed.get('tax_id'),
                        'credit_score': parsed.get('credit_score')
                    }
        except Exception:
            pass
        return { 'tax_id': 'GST12345', 'credit_score': 700 }

    def fetch_pos(self, vendor_name: str):
        # mock: return empty or a candidate
        return [ { 'po_id': 'PO-9001', 'amount': 12000 } ]

    def post_to_erp(self, entries):
        return { 'posted': True, 'erp_txn_id': 'TXN-555' }

    def notify(self, parties, message):
        return { 'ok': True }


# Simple match engine
def compute_match_score(invoice, pos):
    # Very simple comparator: if any PO amount within 5% -> high score
    inv_amt = invoice.get('amount', 0)
    if not pos:
        return 0.0
    for p in pos:
        po_amt = p.get('amount', 0)
        diff = abs(inv_amt - po_amt)
        pct = diff / max(po_amt, 1)
        if pct <= 0.05:
            return 0.95
    return 0.3
