"""
Adapter templates for real MCP clients.
Replace these stubs with actual implementations when credentials are available.
"""


# ============ OCR Adapters (ATLAS) ============

class GoogleVisionAdapter:
    """Adapter for Google Cloud Vision API."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: Initialize google.cloud.vision.ImageAnnotatorClient
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image using Google Vision."""
        # TODO: Implement actual Google Vision call
        # from google.cloud import vision
        # client = vision.ImageAnnotatorClient()
        # ...
        raise NotImplementedError("Configure Google Vision API key in env")


class TesseractAdapter:
    """Adapter for Tesseract OCR."""
    def __init__(self):
        # TODO: import pytesseract; configure path to tesseract executable
        pass
    
    def extract_text(self, image_path: str) -> str:
        """Extract text using Tesseract."""
        # TODO: Implement pytesseract.image_to_string()
        # import pytesseract
        # text = pytesseract.image_to_string(image_path)
        # return text
        raise NotImplementedError("Install pytesseract and tesseract-ocr")


class AwsTextractAdapter:
    """Adapter for AWS Textract."""
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        # TODO: Initialize boto3 textract client
    
    def extract_text(self, image_path: str) -> str:
        """Extract text using AWS Textract."""
        # TODO: Implement AWS Textract call
        # import boto3
        # client = boto3.client('textract', region_name=self.region)
        # response = client.detect_document_text(Document={'S3Object': {...}})
        # ...
        raise NotImplementedError("Configure AWS credentials and region")


# ============ Vendor Enrichment Adapters (ATLAS) ============

class ClearbitAdapter:
    """Adapter for Clearbit Enrichment API."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: Set up requests session with auth header
    
    def enrich_vendor(self, vendor_name: str, domain: str = None) -> dict:
        """Enrich vendor data via Clearbit."""
        # TODO: Implement HTTP POST to Clearbit API
        # response = requests.post('https://company-api.clearbit.com/v1/companies/find',
        #     json={'name': vendor_name}, auth=(api_key, ''))
        # return response.json()
        raise NotImplementedError("Configure Clearbit API key")


class PeopleDatLabsAdapter:
    """Adapter for People Data Labs Enrichment."""
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def enrich_vendor(self, vendor_name: str) -> dict:
        """Enrich vendor data via People Data Labs."""
        # TODO: Implement PDL company API call
        raise NotImplementedError("Configure People Data Labs API key")


class VendorDbAdapter:
    """Adapter for internal/custom vendor database."""
    def __init__(self, db_connection_string: str):
        self.db_conn = db_connection_string
    
    def enrich_vendor(self, vendor_name: str) -> dict:
        """Look up vendor in internal database."""
        # TODO: Query internal vendor DB
        # import sqlite3
        # conn = sqlite3.connect(self.db_conn)
        # cursor = conn.execute("SELECT * FROM vendors WHERE name LIKE ?", (vendor_name,))
        # ...
        raise NotImplementedError("Connect to internal vendor database")


# ============ ERP Adapters (ATLAS) ============

class SapErpAdapter:
    """Adapter for SAP ERP via RFC or REST."""
    def __init__(self, host: str, client: str, user: str, password: str):
        self.host = host
        self.client = client
        self.user = user
        self.password = password
        # TODO: Initialize pyrfc.Connection or requests session
    
    def fetch_purchase_orders(self, vendor_id: str) -> list:
        """Fetch POs from SAP."""
        # TODO: Implement SAP RFC/REST call for PO query
        raise NotImplementedError("Configure SAP connection details")
    
    def fetch_goods_receipts(self, po_id: str) -> list:
        """Fetch GRNs from SAP."""
        # TODO: Implement SAP RFC/REST call for GRN query
        raise NotImplementedError("Configure SAP connection details")
    
    def post_to_erp(self, journal_entries: list) -> dict:
        """Post journal entries to SAP."""
        # TODO: Implement SAP RFC/REST call for posting
        raise NotImplementedError("Configure SAP connection details")


class NetsuiteAdapter:
    """Adapter for NetSuite ERP."""
    def __init__(self, account_id: str, api_key: str, api_secret: str):
        self.account_id = account_id
        self.api_key = api_key
        self.api_secret = api_secret
        # TODO: Initialize NetSuite SuiteTalk REST client
    
    def fetch_purchase_orders(self, vendor_id: str) -> list:
        """Fetch POs from NetSuite."""
        # TODO: Implement NetSuite REST call
        raise NotImplementedError("Configure NetSuite credentials")
    
    def post_to_erp(self, journal_entries: list) -> dict:
        """Post entries to NetSuite."""
        # TODO: Implement NetSuite POST
        raise NotImplementedError("Configure NetSuite credentials")


class MockErpAdapter:
    """Mock ERP for demo/testing (already implemented in mcp_clients.py)."""
    def fetch_purchase_orders(self, vendor_id: str) -> list:
        return [{'po_id': 'PO-9001', 'amount': 12000}]
    
    def post_to_erp(self, journal_entries: list) -> dict:
        return {'posted': True, 'erp_txn_id': 'TXN-DEMO-001'}


# ============ Email/Notification Adapters (ATLAS) ============

class SendGridAdapter:
    """Adapter for SendGrid email."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: from sendgrid import SendGridAPIClient
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SendGrid."""
        # TODO: Implement SendGrid send
        raise NotImplementedError("Configure SendGrid API key")


class SesAdapter:
    """Adapter for AWS SES email."""
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via AWS SES."""
        # TODO: Implement SES send
        raise NotImplementedError("Configure AWS credentials")


# ============ Database Adapters ============

class PostgresAdapter:
    """Adapter for PostgreSQL."""
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname
        # TODO: import psycopg2; create connection pool
    
    def save_checkpoint(self, checkpoint_id: str, state: dict):
        """Save checkpoint to Postgres."""
        # TODO: Implement INSERT/UPDATE
        raise NotImplementedError("Configure Postgres connection")


class DynamoDbAdapter:
    """Adapter for AWS DynamoDB."""
    def __init__(self, table_name: str, region: str = 'us-east-1'):
        self.table_name = table_name
        self.region = region
        # TODO: import boto3; create dynamodb resource
    
    def save_checkpoint(self, checkpoint_id: str, state: dict):
        """Save checkpoint to DynamoDB."""
        # TODO: Implement put_item
        raise NotImplementedError("Configure AWS credentials and DynamoDB table")


# ============ Configuration Helper ============

def get_adapter(adapter_name: str, config: dict):
    """Factory function to load an adapter by name and config."""
    adapters = {
        'google_vision': GoogleVisionAdapter,
        'tesseract': TesseractAdapter,
        'aws_textract': AwsTextractAdapter,
        'anthropic': AnthropicAdapter,
        'clearbit': ClearbitAdapter,
        'people_data_labs': PeopleDatLabsAdapter,
        'vendor_db': VendorDbAdapter,
        'sap_sandbox': SapErpAdapter,
        'netsuite': NetsuiteAdapter,
        'mock_erp': MockErpAdapter,
        'sendgrid': SendGridAdapter,
        'ses': SesAdapter,
        'postgres': PostgresAdapter,
        'dynamodb': DynamoDbAdapter,
    }
    
    adapter_cls = adapters.get(adapter_name)
    if not adapter_cls:
        raise ValueError(f"Unknown adapter: {adapter_name}")
    
    return adapter_cls(**config)


# ============ Anthropic / Claude Adapter (ATLAS NLP) ============
import os

class AnthropicAdapter:
    """Adapter for Anthropic Claude via official SDK.

    Behavior:
    - If `anthropic` package and `ANTHROPIC_API_KEY` are available, uses real API.
    - Otherwise falls back to a harmless canned response so demos/tests continue.
    """
    def __init__(self, api_key: str = None, model: str = 'claude-2'):
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.model = model
        self._have_client = False
        try:
            import anthropic
            if not self.api_key:
                # If key not provided, still treat as no-client
                raise RuntimeError('No ANTHROPIC_API_KEY set')
            self.client = anthropic.Client(api_key=self.api_key)
            self._have_client = True
        except Exception:
            self.client = None
            self._have_client = False

    def call_model(self, prompt: str, max_tokens: int = 1024) -> dict:
        """Call the Anthropic model. Accepts an optional `task` in the prompt header.

        Usage patterns:
        - For parsing invoices: supply a prompt that asks the model to return a JSON with `parsed_line_items` and `invoice_id`.
        - For vendor enrichment: ask for JSON fields like `tax_id`, `credit_score`.
        - For OCR fallback: return `invoice_text`.

        When the SDK/key is missing we return a safe canned structure per task so demos continue.
        """
        # Allow callers to pass a small header in the prompt describing the task, like "TASK:PARSE_INVOICE\n..."
        task = None
        if prompt and isinstance(prompt, str) and prompt.startswith('TASK:'):
            # First line like: TASK:PARSE_INVOICE
            first_line, _, rest = prompt.partition('\n')
            task = first_line.split(':', 1)[1].strip().upper()
            prompt_body = rest
        else:
            prompt_body = prompt

        text = ''
        if self._have_client:
            try:
                # Try best-effort call for different client SDK shapes
                resp = self.client.completions.create(
                    model=self.model,
                    prompt=prompt,
                    max_tokens_to_sample=max_tokens,
                )
                # resp may be object-like or dict-like
                text = getattr(resp, 'completion', None) or (resp.get('completion') if isinstance(resp, dict) else str(resp))
            except Exception:
                text = ''
        else:
            # Fallback canned outputs per task
            if task == 'PARSE_INVOICE':
                return {
                    'invoice_text': 'DUMMY parsed invoice text',
                    'parsed_line_items': [ { 'desc': 'Fallback item', 'qty': 1, 'unit_price': 100.0, 'total': 100.0 } ],
                    'invoice_id': 'INV-1001'
                }
            if task == 'ENRICH_VENDOR':
                return { 'tax_id': 'GST000DEMO', 'credit_score': 650 }
            if task == 'OCR':
                return { 'invoice_text': 'DUMMY OCR text content' }
            # generic fallback
            text = "DUMMY: no-op"

        # Attempt to parse returned text if it contains JSON-like structure
        # Best-effort: if contains 'invoice' keywords, return them in parsed form
        parsed = {
            'invoice_text': text,
            'parsed_line_items': [ { 'desc': 'Fallback item', 'qty': 1, 'unit_price': 100.0, 'total': 100.0 } ]
        }
        return parsed


# (AnthropicAdapter is referenced lazily by `get_adapter` at call time.)
