# Invoice Processing Workflow – LangGraph with HITL Checkpoints

**Status:** ✅ Demo | **Python:** 3.8+ | **Platform:** Windows/Linux/Mac

A fully-implemented **LangGraph-inspired invoice processing agent** with 12 orchestrated stages, Bigtool-based tool selection, MCP client routing, Human-In-The-Loop checkpoints, and checkpoint/resume capabilities.

## Quick Overview

- ✅ 12-stage workflow (INTAKE → COMPLETE) with state propagation
- ✅ Bigtool dynamic tool selection (OCR, enrichment, ERP, DB, email)
- ✅ MCP routing (COMMON & ATLAS server abstractions)
- ✅ HITL checkpoint creation on match failure
- ✅ Flask REST API for human review + interactive UI
- ✅ SQLite checkpoint & audit persistence
- ✅ Full test coverage + CI/CD pipeline
- ✅ Comprehensive documentation (ARCHITECTURE, INTEGRATION_GUIDE, DEMO_GUIDE)

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design, component breakdown, data flow, extension points |
| **[postman_collection.json](postman_collection.json)** | Postman API test collection for human-review endpoints |

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
python.exe -m pip install flask pyyaml pytest
```

### 2. Run Auto-Accept Demo (All 12 Stages)

```powershell
python.exe -m src.runner demo_invoice.json
```

**Output:** Workflow executes all stages, checkpoint created on match failure, auto-resumed, final payload printed.
 
### 3. Run Manual HITL Demo (Pause, Review, Resume)

This project supports a Human-In-The-Loop (HITL) mode where the workflow pauses at checkpoints and waits for a reviewer decision via a small Flask UI.

- **Terminal 1 — Start the Flask human-review API/UI:**

```powershell
python.exe -m src.api_flask
```

- **Terminal 2 — Start the runner in manual mode (no auto-accept):**

```powershell
python.exe -m src.runner demo_invoice.json --no-auto
```

- **Open the browser UI:**

```
http://127.0.0.1:8081/human-review/ui
```

When the runner reaches a checkpoint it will log a pause and the checkpoint ID. Use the browser UI to inspect the pending decision, then click **Accept** or **Reject**. After submitting, the runner will detect the decision and resume execution.

Notes:
- The `--no-auto` flag disables automatic accept/resume so that the workflow stays paused until a human decision is posted.
- The Flask UI endpoints available are `/human-review/pending` and `/human-review/decision` (POST) for programmatic decisions.
- For scripted decisions you can use `scripts/post_decision.py` which writes directly to the DB or calls the API.

