# MasterProjectPlan-BusinessLane

A minimal NCI Hello, World Flask web application, created as the local
baseline for this project before real development begins.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Then open http://127.0.0.1:5000/ in a browser.

## Health check

`GET /health` returns `{"status": "ok"}`.

## Registry

Registered in the [NCI Skills Registry](https://github.com/CBIIT/NCI-Skills-Registry)
as `master-project-plan-business-lane`.
