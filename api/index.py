from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import json, os, numpy as np

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class CheckRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/check")
def check(data: CheckRequest):
    file = "q-vercel-latency.json"
    path = os.path.join(os.path.dirname(__file__), file)
    with open(path, "r") as f:
        telemetry = json.load(f)

    result = {}
    for region in data.regions:
        entries = [e for e in telemetry if e["region"] == region]
        if not entries:
            result[region] = {"avg_latency": 0, "p95": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latencies = [e["latency_ms"] for e in entries]
        uptimes = [e["uptime_pct"] for e in entries]
        breaches = sum(1 for e in entries if e["latency_ms"] > data.threshold_ms)

        result[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 2),
            "breaches": breaches,
        }

    return {"regions": result}

# 👇 Expose a handler for Vercel
from asgiref.wsgi import WsgiToAsgi
import sys
from fastapi.responses import JSONResponse
from starlette.middleware.wsgi import WSGIMiddleware

# vercel expects a "handler" function
handler = WSGIMiddleware(app)
