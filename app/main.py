import csv
import json
import os
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Sysadmin Toolkit API v2")

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
REPORTS_FILE = DATA_DIR / "reports.json"

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

LOG_SUMMARY_CACHE_KEY = "log_summary"
LOG_SUMMARY_TTL_SECONDS = 60
SUSPICIOUS_IPS_KEY = "suspicious_ips"


def load_inventory(filepath: str = "inventory.csv") -> list[dict]:
    try:
        with open(filepath, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="inventory.csv not found")


class Report(BaseModel):
    host: str
    message: str


def load_reports() -> list[dict]:
    if not REPORTS_FILE.exists():
        return []
    return json.loads(REPORTS_FILE.read_text())


@app.post("/reports")
def add_report(report: Report):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    reports = load_reports()
    reports.append(report.model_dump())
    REPORTS_FILE.write_text(json.dumps(reports, indent=2))
    return {"total": len(reports), "reports": reports}


@app.get("/reports")
def list_reports():
    return {"total": len(load_reports()), "reports": load_reports()}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/inventory")
def inventory():
    hosts = load_inventory()
    return {"total": len(hosts), "hosts": hosts}


@app.get("/inventory/vulnerable")
def vulnerable():
    hosts = load_inventory()
    result = [h for h in hosts if "Windows Server" in h["os"] or int(h["ram_gb"]) < 4]
    return {"total": len(result), "hosts": result}


def parse_auth_log(filepath: str = "auth.log") -> dict:
    failed_ips: set[str] = set()
    ip_counts: dict[str, int] = {}

    try:
        with open(filepath) as f:
            for line in f:
                if "Failed password" in line:
                    parts = line.split()
                    if "from" in parts:
                        ip = parts[parts.index("from") + 1]
                        failed_ips.add(ip)
                        ip_counts[ip] = ip_counts.get(ip, 0) + 1
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{filepath} not found")

    return {
        "unique_ips": sorted(failed_ips),
        "counts": ip_counts,
        "total_attempts": sum(ip_counts.values()),
    }


@app.get("/logs/summary")
def logs_summary():
    cached = redis_client.get(LOG_SUMMARY_CACHE_KEY)
    if cached:
        return {"cached": True, **json.loads(cached)}

    summary = parse_auth_log()
    redis_client.set(LOG_SUMMARY_CACHE_KEY, json.dumps(summary), ex=LOG_SUMMARY_TTL_SECONDS)
    return {"cached": False, **summary}


@app.post("/threats/{ip}")
def report_threat(ip: str):
    redis_client.sadd(SUSPICIOUS_IPS_KEY, ip)
    return {"total": redis_client.scard(SUSPICIOUS_IPS_KEY), "suspicious_ips": list(redis_client.smembers(SUSPICIOUS_IPS_KEY))}


@app.get("/threats")
def list_threats():
    ips = list(redis_client.smembers(SUSPICIOUS_IPS_KEY))
    return {"total": len(ips), "suspicious_ips": ips}
