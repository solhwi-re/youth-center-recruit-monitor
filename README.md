# 전국 청년센터 채용공고 모니터링 GPT 서버

전국 청년센터 DB를 기준으로 홈페이지 채용공고 후보를 탐색하고, 신규 공고가 있으면 Gmail로 발송하는 FastAPI 서버입니다.

## 1. 구성

```text
app/
 ├─ main.py        # FastAPI 엔드포인트
 ├─ db_loader.py   # 청년센터 엑셀 DB 로딩
 ├─ crawler.py     # 홈페이지/게시판 후보 탐색
 ├─ mailer.py      # Gmail SMTP 발송
 ├─ state.py       # 발송 URL 중복 체크
 ├─ config.py      # 환경변수/키워드
 └─ models.py      # 데이터 모델

data/
 └─ youth_center_db.xlsx

.github/workflows/
 └─ daily-recruit-monitor.yml  # 매일 오전 9시 예약 호출
```

## 2. 현재 V1 기능

- 청년센터 엑셀 DB 252개소 로딩
- 홈페이지 URL 접속
- 공지/알림/소식/채용/공고/게시판 링크 후보 탐색
- 채용 관련 키워드 포함 여부 판단
- 제외 키워드 적용
- 신규 URL만 필터링
- Gmail SMTP 발송
- My GPT Action용 OpenAPI 스키마 포함

## 3. V1 한계

- 사람인/잡코리아/인크루트 수집은 아직 미포함입니다.
- 일부 사이트는 자바스크립트 렌더링 방식이면 수집되지 않을 수 있습니다.
- Render 무료 Web Service는 로컬 파일이 장기 저장소가 아니므로, 재배포/스핀다운 이후 `data/sent_urls.txt`가 유실될 수 있습니다. 완전한 중복 방지는 V2에서 Google Sheet 또는 외부 DB를 붙이는 것을 권장합니다.

## 4. 로컬 실행

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

상태 확인:

```bash
curl http://localhost:8000/health
```

수동 스캔:

```bash
curl -X POST "http://localhost:8000/scan?limit=20" -H "X-Run-Secret: 임의의_긴_문자열"
```

메일 발송 포함 실행:

```bash
curl -X POST "http://localhost:8000/run?send_email=true" -H "X-Run-Secret: 임의의_긴_문자열"
```

## 5. Render 배포

1. GitHub에 새 저장소 생성
   - 추천 이름: `youth-center-recruit-monitor`
2. 이 폴더 전체 업로드
3. Render에서 New Web Service 생성
4. GitHub 저장소 연결
5. Build Command

```bash
pip install -r requirements.txt
```

6. Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

7. 환경변수 설정

| Key | 설명 |
|---|---|
| RUN_SECRET | 외부 호출 보호용 비밀키 |
| SMTP_HOST | smtp.gmail.com |
| SMTP_PORT | 587 |
| SMTP_USER | 발송용 Gmail 주소 |
| SMTP_PASSWORD | Gmail 앱 비밀번호 |
| MAIL_FROM | 발송자 표시명 |
| MAIL_TO | 수신자 이메일, 쉼표로 여러 명 입력 |
| MAX_CENTERS_PER_RUN | 기본 252 |

## 6. Gmail 설정

Gmail SMTP를 쓰려면 Google 계정에서 앱 비밀번호를 발급해야 합니다.

- Google 계정 2단계 인증 활성화
- 앱 비밀번호 생성
- 생성된 16자리 비밀번호를 `SMTP_PASSWORD`에 입력

기관 계정에서 앱 비밀번호 사용이 막혀 있다면, 별도 발송용 Gmail 계정을 만드는 방식을 권장합니다.

## 7. 무료 예약 실행 방식

Render Cron Job은 유료 과금이 발생할 수 있으므로, 무료 운영은 GitHub Actions가 Render 서버의 `/run` 엔드포인트를 매일 호출하는 방식으로 구성합니다.

GitHub 저장소 Settings → Secrets and variables → Actions → Repository secrets에 아래 2개 추가:

| Secret | 값 |
|---|---|
| RENDER_MONITOR_URL | https://배포주소.onrender.com |
| RUN_SECRET | Render 환경변수와 같은 값 |

`.github/workflows/daily-recruit-monitor.yml` 기준으로 매일 한국시간 09:00에 실행됩니다.

## 8. My GPT 연결

`openapi_my_gpt.json`의 서버 URL을 실제 Render 주소로 바꾼 뒤, My GPT Actions에 붙여넣으면 됩니다.

추천 GPT 지침:

```text
당신은 전국 청년센터 채용공고 모니터링 AI입니다. 사용자가 채용공고 확인을 요청하면 Action의 /scan 또는 /latest를 호출하여 결과를 확인합니다. 결과는 반드시 지역, 센터명, 운영법인, 공고명, URL, 출처 형식으로 정리합니다. 채용공고가 없거나 불확실하면 임의로 만들지 말고 확인된 결과가 없다고 답합니다.
```
