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
