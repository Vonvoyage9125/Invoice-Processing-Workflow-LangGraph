# Invoice Processing Workflow - Architecture & Design

## Overview

This project implements a **LangGraph-like Invoice Processing Agent** that orchestrates a 12-stage workflow for invoice ingestion, validation, enrichment, matching, and posting to ERP systems. The agent supports:

- **Deterministic stages** (sequential logic)
- **Non-deterministic stages** (dynamic ability selection via Bigtool)
- **Human-In-The-Loop (HITL) checkpoints** (pause for manual review, resume after decision)
- **MCP client orchestration** (routing abilities to COMMON and ATLAS servers)
- **Bigtool-based tool selection** (dynamic provider selection for OCR, enrichment, ERP, etc.)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flask Human Review API                   │
│  /human-review/pending, /human-review/decision, /human-review/ui │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ (decision posts)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Runner (src/runner.py)                │
│                                                                   │
│  Sequential stage executor with checkpoint pause/resume          │
│  Nodes: INTAKE → UNDERSTAND → PREPARE → RETRIEVE → MATCH_TWO_WAY │
│         → CHECKPOINT_HITL → HITL_DECISION → RECONCILE → APPROVE  │
│         → POSTING → NOTIFY → COMPLETE                            │
└─────────────────────────────────────────────────────────────────┘
                              ▲▼
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                            │
   ┌────▼────┐                              ┌───────▼─────┐
   │ Nodes   │                              │ Bigtool     │
   │ (12x)   │◄─────────────────────────────┤ Picker      │
   └────┬────┘                              └─────────────┘
        │                                          │
        │ (state propagation)                      │ (tool selection)
        │                                          │
   ┌────▼────────────────────────────────────────┐
   │ MCP Clients (COMMON / ATLAS adapters)       │
   │  - OCR (Google Vision / Tesseract / AWS)    │
   │  - Enrichment (Clearbit / PDL / Vendor DB)  │
   │  - ERP (SAP / NetSuite / Mock)              │
   │  - Email (SendGrid / SES / Mock)            │
   │  - Match Engine                             │
   │  - Accounting Engine                        │
   └────┬────────────────────────────────────────┘
        │
   ┌────▼────────────────────────────────────────┐
   │ Database Layer (SQLite / Postgres / DynamoDB)
   │  - Checkpoint storage                       │
   │  - Audit log                                │
   │  - Decision history                         │
   └─────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. **Workflow Runner** (`src/runner.py`)

**Responsibility:** Sequential orchestration of stages

**Features:**
- Loads workflow definition from `workflow.json`
- Executes stages in order (INTAKE → COMPLETE)
- Propagates state through each node
- Detects checkpoint triggers (match failure)
- Pauses on checkpoint creation
- Polls DB for human decision (if `--no-auto` mode)
- Resumes execution after decision

**Usage:**
```bash
# Auto-decide mode (demo)
E:\Anaconda_new\python.exe -m src.runner demo_invoice.json

# Manual mode (requires external decision)
E:\Anaconda_new\python.exe -m src.runner demo_invoice.json --no-auto
```

---

### 2. **Workflow Nodes** (`src/nodes.py`)

**12 Node Types:**

| Stage | Node Class | Mode | Server(s) | Input | Output |
|-------|-----------|------|-----------|-------|--------|
| INTAKE | IngestNode | Deterministic | COMMON | invoice payload | raw_id, ingest_ts |
| UNDERSTAND | OcrNlpNode | Deterministic | COMMON/ATLAS | attachments | parsed_invoice |
| PREPARE | NormalizeEnrichNode | Deterministic | COMMON/ATLAS | vendor_name | vendor_profile, flags |
| RETRIEVE | ErpFetchNode | Deterministic | ATLAS | vendor_name | matched_pos, matched_grns |
| MATCH_TWO_WAY | TwoWayMatcherNode | Deterministic | COMMON | invoice, pos | match_score, match_result |
| CHECKPOINT_HITL | CheckpointNode | Deterministic | COMMON | state | checkpoint_id, review_url |
| HITL_DECISION | HumanReviewNode | Non-deterministic | (external) | checkpoint | human_decision |
| RECONCILE | ReconciliationNode | Deterministic | COMMON | invoice | accounting_entries |
| APPROVE | ApprovalNode | Deterministic | ATLAS/policy | amount, rules | approval_status |
| POSTING | PostingNode | Deterministic | ATLAS | entries | posted, erp_txn_id |
| NOTIFY | NotifyNode | Deterministic | ATLAS | state | notify_status |
| COMPLETE | CompleteNode | Deterministic | COMMON | state | final_payload, audit_log |

**State Propagation:**
- Each node receives full state dict
- Node processes and enriches state
- State passed to next node
- Audit entries logged per stage

---

### 3. **Bigtool Picker** (`src/bigtool.py`)

**Purpose:** Dynamically select tool implementations from pools

**Pools Configured:**
```yaml
ocr: [google_vision, tesseract, aws_textract]
enrichment: [clearbit, people_data_labs, vendor_db]
erp_connector: [sap_sandbox, netsuite, mock_erp]
db: [sqlite, postgres, dynamodb]
email: [sendgrid, ses]
```

**Usage in Nodes:**
```python
pick = self.bigtool.select('ocr')  # Returns first available tool in pool
self.log(invoice_id, stage, f"Bigtool selected: {pick}")
```

**Future Enhancement:** Can route to real adapter instances based on config/env.

---

### 4. **MCP Clients & Adapters** (`src/mcp_clients.py`, `src/adapters.py`)

**Current Implementation:**
- **MockCommonClient**: Simulates COMMON server abilities (normalize, enrich, compute, etc.)
- **MockAtlasClient**: Simulates ATLAS server abilities (OCR, ERP fetch, posting, etc.)
- **MatchEngine**: Simple 2-way match logic (invoice vs PO amount comparison)

**Adapter Templates** (`src/adapters.py`):
- **OCR**: GoogleVisionAdapter, TesseractAdapter, AwsTextractAdapter
- **Enrichment**: ClearbitAdapter, PeopleDatLabsAdapter, VendorDbAdapter
- **ERP**: SapErpAdapter, NetsuiteAdapter, MockErpAdapter
- **Email**: SendGridAdapter, SesAdapter
- **Database**: PostgresAdapter, DynamoDbAdapter

**To Wire Real Adapters:**
1. Install SDK: `pip install google-cloud-vision` (example)
2. Set credentials in env vars or config.yaml
3. Update nodes to instantiate adapter instead of mock client
4. Test with `INTEGRATION_GUIDE.md`

---

### 5. **Database Layer** (`src/db.py`)

**Tables:**
- **checkpoints** (id, invoice_id, state_blob, status, created_at, updated_at, reviewer_id, decision)
- **audit_log** (id, invoice_id, stage, message, ts)

**Key Functions:**
- `init_db()` — Create/connect to DB
- `save_checkpoint()` — Persist state to checkpoint
- `list_pending()` — List PAUSED checkpoints
- `fetch_checkpoint()` — Fetch a checkpoint by ID
- `save_decision()` — Record human decision
- `mark_completed()` — Update checkpoint status
- `append_audit()` — Log stage transitions

**Database Providers:**
- **SQLite** (default, portable)
- **PostgreSQL** (production-grade)
- **DynamoDB** (serverless, AWS)

---

### 6. **Human Review API** (`src/api_flask.py`)

**Endpoints:**

**GET `/human-review/pending`**
- Lists all PAUSED checkpoints
- Response: Array of pending items with checkpoint_id, invoice_id, amount, vendor_name, created_at

**POST `/human-review/decision`**
- Accepts: `{ checkpoint_id, decision, reviewer_id }`
- Decision: "ACCEPT" or "REJECT"
- Updates checkpoint status to DECIDED
- Marks checkpoint completed

**GET `/human-review/ui`**
- Serves simple HTML UI (static/ui.html)
- Displays pending checkpoints in a table
- Accept/Reject buttons POST decisions

**Configuration:**
- Host: 127.0.0.1 (localhost)
- Port: 8081 (configurable)

---

### 7. **Logging & Audit** (`src/logging_utils.py`)

**WorkflowLogger:**
- Tracks stage transitions
- Records tool selections (Bigtool)
- Logs ability calls (MCP)
- Timestamps all events
- Exports events as JSON

**Output:**
- Console (real-time)
- File (`workflow.log`)
- Database (audit_log table)

**Usage:**
```python
logger = WorkflowLogger(invoice_id='INV-001')
logger.log_stage_start('UNDERSTAND', 'UNDERSTAND')
logger.log_tool_selection('ocr', 'google_vision', context={...})
logger.log_checkpoint_created('uuid', 'match_score < threshold')
logger.export_events_to_file('events.json')
```

---

## Data Flow Example (Happy Path)

```
1. User provides invoice JSON to runner
   ↓
2. INTAKE: Validate & persist raw payload
   ↓
3. UNDERSTAND: Extract text via OCR (Bigtool picks google_vision/tesseract/aws)
   ↓
4. PREPARE: Normalize vendor, enrich via Clearbit/PDL, compute flags
   ↓
5. RETRIEVE: Fetch POs from SAP/NetSuite (Bigtool picks ERP connector)
   ↓
6. MATCH_TWO_WAY: Compare invoice vs PO, compute match_score
   ↓
   IF match_score >= 0.90: Continue to RECONCILE
   ELSE: Proceed to checkpoint
   ↓
7. CHECKPOINT_HITL: Save state to DB, create review entry
   ↓
8. [PAUSE] Runner waits for human decision via Flask API
   ↓
   Human reviews via UI, clicks "Accept"
   ↓
9. Runner detects decision, resumes
   ↓
10. RECONCILE: Build accounting entries
    ↓
11. APPROVE: Auto-approve or escalate
    ↓
12. POSTING: Post to ERP, schedule payment
    ↓
13. NOTIFY: Send email/Slack to vendor and finance
    ↓
14. COMPLETE: Generate final payload
    ↓
15. Workflow done. Audit log and checkpoint marked COMPLETED.
```

---

## Checkpoint & Resume Flow (HITL)

```
┌──────────────────────────────────────────────────────────┐
│ Workflow execution pauses when:                          │
│ - match_score < threshold (default 0.90)               │
└──────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│ CheckpointNode saves:                                   │
│ - Full state blob (invoice, enrichment, match data)    │
│ - Checkpoint ID (UUID)                                  │
│ - Status: PAUSED                                        │
│ - Created timestamp                                      │
└──────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Runner enters polling loop:                             │
│ - Queries DB every 1 second                            │
│ - Checks if checkpoint status changed from PAUSED      │
│ - Waits for DECIDED status                             │
└──────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Human reviews via Flask UI:                             │
│ - Lists pending checkpoints                             │
│ - Shows invoice details (amount, vendor)               │
│ - Clicks "Accept" or "Reject"                          │
└──────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Flask API:                                              │
│ - POST /human-review/decision                          │
│ - Updates DB: status=DECIDED, decision=ACCEPT/REJECT  │
│ - Marks timestamp                                       │
└──────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Runner detects decision:                                │
│ - If ACCEPT: Resume from RECONCILE                     │
│ - If REJECT: Finalize with REQUIRES_MANUAL_HANDLING   │
└──────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Workflow resumes or completes                           │
└──────────────────────────────────────────────────────────┘
```

---

## File Structure

```
Invoice_Processing_Workflow/
├── ProjectOverview.md               # Original task description
├── workflow.json                    # Workflow stage definitions
├── tools.yaml                       # Bigtool pool configuration
├── demo_invoice.json                # Sample invoice for testing
├── requirements.txt                 # Python dependencies
├── README.md                        # Quick start guide
├── ARCHITECTURE.md                  # This file
├── postman_collection.json          # Postman API collection
├── .gitignore
├── .github/
│   └── workflows/
│       └── tests.yml               # GitHub Actions CI
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── runner.py                   # Stage orchestrator
│   ├── nodes.py                    # 12 node implementations
│   ├── db.py                       # Database helpers
│   ├── bigtool.py                  # Tool selector
│   ├── mcp_clients.py              # Mock COMMON/ATLAS clients
│   ├── adapters.py                 # Real adapter templates
│   ├── api_flask.py                # Flask human-review API
│   ├── logging_utils.py            # Structured logging
│   └── static/
│       └── ui.html                 # Human review UI
├── tests/
│   ├── __init__.py
│   └── test_workflow.py            # Unit & integration tests
└── demo.db                         # SQLite database (runtime)
```

---

## Key Design Decisions

1. **Sequential Stage Execution**: Stages run in order; state propagates end-to-end. This ensures deterministic flow and full auditability.

2. **Checkpoint at Match Failure**: Only when 2-way matching fails do we pause and wait for human decision. This minimizes manual intervention for happy-path invoices.

3. **Bigtool Abstraction**: Tool selection is decoupled from node logic. Nodes don't need to know which OCR/ERP provider is active; Bigtool handles it.

4. **State Blob Persistence**: The entire workflow state is serialized and stored in DB on checkpoint. This enables full resume capability—no logic loss.

5. **Flask over async**: A simple Flask API enables easy HTTP testing and UI integration without adding async complexity.

6. **Mock Clients for Demo**: Real adapters are templatized but optional. Demo mode uses mocks so you don't need credentials to try the workflow.

7. **Audit-First Logging**: Every decision, tool selection, and state transition is logged. Critical for regulatory compliance and debugging.

---

## Extension Points

**To add new stages:**

1. Create a new Node class in `src/nodes.py`
2. Add entry to `workflow.json`
3. Update `NODE_MAP` in `runner.py`
4. Add tests in `tests/test_workflow.py`

---

## Testing Strategy

**Unit Tests** (`tests/test_workflow.py`):
- Node state propagation
- Checkpoint persistence
- Bigtool selection
- Audit logging

**Integration Tests**:
- Full workflow (auto-accept)
- Workflow with manual HITL pause/resume
- Error handling and recovery

**CI/CD** (`.github/workflows/tests.yml`):
- Runs tests on Python 3.8–3.11
- Generates coverage reports
- Lints code with flake8

---

## Deployment Considerations

**Development:**
- SQLite (included, no setup)
- Mock clients (no credentials needed)
- Flask development server (8081)

**Production:**
- PostgreSQL or DynamoDB for DB
- Real adapters (Google Vision, SAP, Clearbit, etc.)
- WSGI server (Gunicorn, uWSGI) for Flask
- Kubernetes or serverless (AWS Lambda) for scaling
- Monitoring: logs, metrics, alerts
- Security: API keys in Vault/Secrets Manager, TLS/SSL, rate limiting

---

## Next Steps

1. **Integrate real adapters** using `INTEGRATION_GUIDE.md`
2. **Deploy** Flask API and runner to production environment
3. **Monitor** via logs and audit trail
4. **Iterate** based on feedback


