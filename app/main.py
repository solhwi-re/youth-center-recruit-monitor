from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from .config import RUN_SECRET, MAX_CENTERS_PER_RUN
from .db_loader import load_centers
from .crawler import scan_centers
from .state import filter_new
from .mailer import send_recruit_email, format_posts

app = FastAPI(
    title="Youth Center Recruit Monitor",
    version="1.2.0",
    description="전국 청년센터 홈페이지 기반 채용공고 모니터링 API",
)


def check_secret(x_run_secret: str | None):
    if RUN_SECRET and x_run_secret != RUN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid RUN_SECRET")


@app.get("/health")
def health():
    centers = load_centers()
    return {
        "ok": True,
        "center_count": len(centers),
    }


@app.get("/centers")
def centers(limit: int = Query(20, ge=1, le=300)):
    data = load_centers()[:limit]

    return {
        "count": len(data),
        "results": [c.model_dump() for c in data],
    }


@app.post("/scan")
def scan(
    limit: int = Query(MAX_CENTERS_PER_RUN, ge=1, le=300),
    x_run_secret: str | None = Header(default=None),
):
    check_secret(x_run_secret)

    centers = load_centers()

    if limit >= len(centers):
        target_centers = centers
    else:
        target_centers = centers[:limit]

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

    centers = load_centers()

    if limit >= len(centers):
        target_centers = centers
    else:
        target_centers = centers[:limit]

    posts = scan_centers(target_centers)
    new_posts = filter_new(posts)

    email_result = {
        "sent": False,
        "reason": "send_email=false",
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

    centers = load_centers()

    if limit >= len(centers):
        target_centers = centers
    else:
        target_centers = centers[:limit]

    posts = scan_centers(target_centers)

    return format_posts(posts)
