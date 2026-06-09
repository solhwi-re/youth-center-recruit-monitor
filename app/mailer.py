from __future__ import annotations

import smtplib
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM, MAIL_TO
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
    if not SMTP_USER or not SMTP_PASSWORD:
        return {"sent": False, "reason": "SMTP_USER 또는 SMTP_PASSWORD가 설정되지 않았습니다."}

    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    msg = EmailMessage()
    msg["Subject"] = f"[전국 청년센터 채용공고 알림] 신규 채용공고 {len(posts)}건 ({today})"
    msg["From"] = MAIL_FROM or SMTP_USER
    msg["To"] = ", ".join(to_list)
    msg.set_content(format_posts(posts))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)
    return {"sent": True, "to": to_list, "count": len(posts)}
