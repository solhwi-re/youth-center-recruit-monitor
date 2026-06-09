import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "youth_center_db.xlsx"
STATE_PATH = BASE_DIR / "data" / "sent_urls.txt"

INCLUDE_KEYWORDS = [
    "채용", "채용공고", "직원채용", "직원모집", "인력채용", "구인", "모집공고",
    "기간제", "계약직", "정규직", "센터장", "팀장", "매니저", "청년매니저",
    "청년지원매니저", "직원 모집", "종사자 모집", "사업전담인력", "전담인력",
    "행정인력", "행정지원인력", "코디네이터",
]

EXCLUDE_KEYWORDS = [
    "참여자 모집", "교육생 모집", "멘토 모집", "청년 모집", "수강생 모집",
    "서포터즈 모집", "기자단 모집", "자원봉사자 모집", "프로그램 참여자",
]

MENU_KEYWORDS = [
    "공지", "알림", "소식", "채용", "공고", "게시판", "열린마당", "새소식", "센터소식"
]

RUN_SECRET = os.getenv("RUN_SECRET", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)
MAIL_TO = [x.strip() for x in os.getenv("MAIL_TO", "").split(",") if x.strip()]
MAX_CENTERS_PER_RUN = int(os.getenv("MAX_CENTERS_PER_RUN", "252"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; YouthCenterRecruitMonitor/1.0; +https://example.com)",
)
