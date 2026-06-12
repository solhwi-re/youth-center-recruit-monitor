
`config.py` 전체를 아래 내용으로 **통째로 교체**해주세요. 코드블록 표시 없이, 내용만 넣으시면 됩니다.

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "youth_center_db.xlsx"
STATE_PATH = BASE_DIR / "data" / "sent_urls.txt"

INCLUDE_KEYWORDS = [
    "청년지원매니저", "청년 지원 매니저", "청년매니저", "청년 매니저",
    "청년코디", "청년 코디", "매니저", "팀원", "팀장", "센터장",
    "사무국장", "전담인력", "사업전담인력", "코디네이터",
    "직원채용", "직원 채용", "직원모집", "직원 모집",
    "근로자 채용", "종사자 모집", "채용공고", "채용 공고",
    "채용 재공고", "정규직", "계약직", "기간제",
    "기간제근로자", "기간제 근로자",
]

EXCLUDE_KEYWORDS = [
    "최종합격", "최종 합격", "합격자", "면접심사", "면접 심사",
    "면접대상", "면접 대상", "서류전형", "서류 전형",
    "결과공고", "결과 공고", "결과 안내", "채용결과",
    "채용 결과", "발표",

    "참여자 모집", "교육생 모집", "멘토 모집", "청년 모집",
    "수강생 모집", "서포터즈 모집", "기자단 모집",
    "자원봉사자 모집", "프로그램 참여자",

    "채용정보", "청년채용정보", "구인구직", "구인·구직",
    "취업정보", "취업패키지", "채용박람회", "채용 설명회",

    "생산직", "생산기사", "품질팀", "마케팅", "디자인",
    "전산팀", "구매팀", "PLC", "전기기사",
]

MENU_KEYWORDS = [
    "공지", "공지사항", "채용", "채용공고", "공고",
    "알림", "소식", "새소식", "센터소식",
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
    "Mozilla/5.0 (compatible; YouthCenterRecruitMonitor/1.0)"
)
