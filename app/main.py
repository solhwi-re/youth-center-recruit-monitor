import json
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from .config import RUN_SECRET, MAX_CENTERS_PER_RUN
from .db_loader import load_centers
from .crawler import scan_centers
from .state import filter_new
from .mailer import send_recruit_email, format_posts

app = FastAPI(
    title="Youth Center Recruit Monitor",
    version="1.3.0",
    description="전국 청년센터 홈페이지 기반 채용공고 모니터링 API",
)

BASE_DIR = Path(__file__).resolve().parents[1]
LATEST_JOBS_PATH = BASE_DIR / "data" / "latest_jobs.json"


def check_secret(x_run_secret: str | None):
    if RUN_SECRET and x_run_secret != RUN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid RUN_SECRET")


def save_latest_jobs(posts):
    LATEST_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "count": len(posts),
        "results": [p.model_dump() for p in posts],
    }

    with open(LATEST_JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_latest_jobs():
    if not LATEST_JOBS_PATH.exists():
        return {
            "count": 0,
            "results": [],
            "message": "아직 저장된 채용공고 조회 결과가 없습니다. 먼저 /run을 실행해 주세요.",
        }

    with open(LATEST_JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def select_centers(limit: int):
    centers = load_centers()

    if limit >= len(centers):
        target_centers = centers
    else:
        target_centers = centers[:limit]

    return centers, target_centers


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Youth Center Recruit Monitor",
        "docs": "/docs",
        "health": "/health",
        "jobs": "/jobs",
    }


@app.get("/health")
def health():
    centers = load_centers()
    latest = load_latest_jobs()

    return {
        "ok": True,
        "center_count": len(centers),
        "latest_jobs_count": latest.get("count", 0),
    }


@app.get("/centers")
def centers(limit: int = Query(20, ge=1, le=300)):
    data = load_centers()[:limit]

    return {
        "count": len(data),
        "results": [c.model_dump() for c in data],
    }


@app.get("/jobs")
def jobs(
    region: str | None = Query(None, description="지역명 필터 예: 서울, 인천, 부산"),
    keyword: str | None = Query(None, description="키워드 필터 예: 청년지원매니저, 센터장, 팀장"),
):
    latest = load_latest_jobs()
    results = latest.get("results", [])

    if region:
        results = [
            item for item in results
            if region in (item.get("region") or "")
        ]

    if keyword:
        results = [
            item for item in results
            if keyword in (item.get("title") or "")
            or keyword in (item.get("center_name") or "")
            or keyword in (item.get("matched_keyword") or "")
        ]

    return {
        "count": len(results),
        "results": results,
    }


@app.post("/scan")
def scan(
    limit: int = Query(MAX_CENTERS_PER_RUN, ge=1, le=300),
    x_run_secret: str | None = Header(default=None),
):
    check_secret(x_run_secret)

    centers, target_centers = select_centers(limit)
    posts = scan_centers(target_centers)

    return {
        "scanned_centers": len(target_centers),
        "total_centers": len(centers),
        "found_count": len(posts),
        "results": [p.model_dump() for p in posts],
    }


@app.post("/run")
def run(
    limit: int = Query(MAX_CENTERS_PER_RUN, ge=1, le=300),
    send_email: bool = Query(True),
    x_run_secret: str | None = Header(default=None),
):
    check_secret(x_run_secret)

    centers, target_centers = select_centers(limit)
    posts = scan_centers(target_centers)

    save_latest_jobs(posts)

    new_posts = filter_new(posts)

    email_result = {
        "sent": False,
        "reason": "send_email=false 또는 신규 채용공고 없음",
    }

    if send_email and new_posts:
        email_result = send_recruit_email(new_posts)

    return {
        "scanned_centers": len(target_centers),
        "total_centers": len(centers),
        "found_count": len(posts),
        "new_count": len(new_posts),
        "email": email_result,
        "results": [p.model_dump() for p in new_posts],
    }


@app.get("/latest", response_class=PlainTextResponse)
def latest(
    limit: int = Query(MAX_CENTERS_PER_RUN, ge=1, le=300),
    x_run_secret: str | None = Header(default=None),
):
    check_secret(x_run_secret)

    centers, target_centers = select_centers(limit)
    posts = scan_centers(target_centers)

    return format_posts(posts)
