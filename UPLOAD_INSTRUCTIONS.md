UPLOAD_INSTRUCTIONS

This folder (`Github/`) is prepared for uploading to GitHub. It contains the project sources, configs, docs, and helpers needed to run the demo locally.


Post-clone setup (quick)
1. Install dependencies (use your Python environment):

```powershell
python -m pip install -r requirements.txt
```

2. Start the human-review API (Terminal 1):

```powershell
python -m src.api_flask
```

3. Start the runner (Terminal 2) — manual HITL:

```powershell
python -m src.runner demo_invoice.json --no-auto
```

4. Open the review UI in your browser:

```
http://127.0.0.1:8081/human-review/ui
```
