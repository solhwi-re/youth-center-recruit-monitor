from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import resend

from .config import MAIL_FROM, MAIL_TO, RESEND_API_KEY
from .models import RecruitPost


def format_posts(posts: list[RecruitPost]) -> str:
    if not posts:
        return "신규 채용공고가 발견되지 않았습니다."

    lines = ["📢 신규 채용공고가 발견되었습니다.", ""]

    for p in posts:
        lines.extend([
            f"📍 {p.region}",
            f"🏢 {p.center_name}",
            f"🏛️ 운영법인: {p.operator_name or '-'}",
            f"📌 {p.title}",
            f"🔗 {p.url}",
            f"📍 출처: {p.source}",
            "────────────────────",
        ])

    lines.append(f"총 {len(posts)}건")
    return "\n".join(lines)


def send_recruit_email(posts: list[RecruitPost], recipients: list[str] | None = None) -> dict:
    to_list = recipients or MAIL_TO

    if not to_list:
        return {"sent": False, "reason": "MAIL_TO가 설정되지 않았습니다."}

    if not RESEND_API_KEY:
        return {"sent": False, "reason": "RESEND_API_KEY가 설정되지 않았습니다."}

    if not MAIL_FROM:
        return {"sent": False, "reason": "MAIL_FROM이 설정되지 않았습니다."}

    resend.api_key = RESEND_API_KEY

    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    subject = f"[전국 청년센터 채용공고 알림] 신규 채용공고 {len(posts)}건 ({today})"
    body = format_posts(posts)

    response = resend.Emails.send({
        "from": MAIL_FROM,
        "to": to_list,
        "subject": subject,
        "text": body,
    })

    return {
        "sent": True,
        "to": to_list,
        "count": len(posts),
        "resend_id": response.get("id") if isinstance(response, dict) else None,
    }
