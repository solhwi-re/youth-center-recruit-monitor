from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode
import requests
from bs4 import BeautifulSoup

from .config import INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS, MENU_KEYWORDS, REQUEST_TIMEOUT, USER_AGENT
from .models import Center, RecruitPost


def is_probably_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def normalize_url(url: str) -> str:
    return url.strip()


def normalize_post_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        remove_keys = {
            "q", "field", "wrd", "search", "search_key", "keyword",
            "page", "offset", "sk", "sw", "category", "cate1",
            "search_first_subject", "list_mode", "auto_frame", "me_popup",
            "from", "fromNxList", "searchType", "placePath", "entry",
            "mNum", "sNum", "cate_sub_idx", "me_co",
        }

        query_items = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key in remove_keys:
                continue
            query_items.append((key, value))

        new_query = urlencode(query_items, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            "",
        ))
    except Exception:
        return url


def is_external_or_social(url: str) -> bool:
    lowered = url.lower()
    return any(x in lowered for x in [
        "instagram.com", "facebook.com", "youtube.com", "map.naver.com", "naver.me",
        "pf.kakao.com", "kakaotalk", "blog.naver.com"
    ])


def is_bad_url(url: str) -> bool:
    lowered = (url or "").lower()
    return any(x in lowered for x in [
        "down.html", "download", "filedown", "file_down",
        "post_file_download", "bbsmsgfiledown",
        ".pdf", ".hwp", ".hwpx", ".png", ".jpg", ".jpeg",
        "work24.go.kr", "jobaba.net", "apply.jobaba",
    ])


def is_generic_menu_title(title: str) -> bool:
    compact = re.sub(r"\s+", "", title or "")
    return compact in {
        "채용공고", "공고", "공지", "공지사항", "알림", "소식",
        "새소식", "센터소식", "게시판", "열린마당"
    }


def keyword_hit(text: str) -> tuple[bool, str | None]:
    compact = re.sub(r"\s+", " ", text or "")

    result_words = [
        "합격", "최종합격", "서류합격", "면접전형 결과", "면접 결과",
        "필기시험 결과", "전형 결과", "결과 발표", "결과 공고",
    ]
    if any(x in compact for x in result_words):
        return False, None

    for bad in EXCLUDE_KEYWORDS:
        if bad in compact:
            return False, None

    center_related = [
        "청년센터", "청년지원센터", "청년공간", "청년청", "청년마루",
        "청년내일", "청년일삶센터", "청년지원매니저", "청년코디",
        "청년시설", "청년뜰", "청년시청", "청년모아", "청년정주지원센터",
        "청년사이", "청정지대", "청년가온마당", "유유기지",
    ]

    for good in INCLUDE_KEYWORDS:
        if good in compact:
            if any(x in compact for x in center_related) or "청년" in compact:
                return True, good

    return False, None


def is_likely_recruit_post(title: str, url: str) -> bool:
    if is_bad_url(url):
        return False

    if is_generic_menu_title(title):
        return False

    compact = re.sub(r"\s+", " ", title or "")

    result_words = [
        "합격", "최종합격", "서류합격", "면접전형 결과", "면접 결과",
        "필기시험 결과", "전형 결과", "결과 발표", "결과 공고",
    ]
    if any(x in compact for x in result_words):
        return False

    if any(year in compact for year in ["2025", "2024", "2023", "2022", "2021"]):
        return False

    bad_signals = [
        "후기", "감사합니다", "지원사업", "장려금", "학자금", "장학금",
        "취업 역량", "업무협약", "사업안내", "채용지원 모집중",
        "청년정규직 내일지원사업", "기간제·파견근로자 출산전후휴가",
        "통합채용", "통합 채용", "일자리", "구인", "워크넷", "워크24",
        "jobaba", "잡아바", "공공기관 통합채용", "채용관",
        "정신건강복지센터", "육아종합지원센터", "사회적경제지원센터",
        "농촌활력지원센터", "농업기술센터", "보건소",
        "품질관리", "생산", "CNC", "조리파트", "골프클럽", "스파비스",
        "전임의사", "공장", "품질보증", "환경관리원", "청소지원인력",
        "청소환경관리", "하천관리원", "공원관리", "안전경비원",
        "대체교사", "photo file", "photo", "file",
        "~01", "~02", "~03", "~04", "~05", "~06",
        "~07", "~08", "~09", "~10", "~11", "~12",
    ]
    if any(bad in compact for bad in bad_signals):
        return False

    recruit_signals = [
        "채용", "모집", "공고", "재공고", "직원", "근로자",
        "매니저", "코디", "전담인력", "청년지원매니저", "청년코디"
    ]
    if not any(signal in compact for signal in recruit_signals):
        return False

    center_related = [
        "청년센터", "청년지원센터", "청년공간", "청년청", "청년마루",
        "청년내일", "청년일삶센터", "청년지원매니저", "청년코디",
        "청년시설", "청년뜰", "청년시청", "청년모아", "청년정주지원센터",
        "청년사이", "청정지대", "청년가온마당", "유유기지",
    ]
    if not (any(x in compact for x in center_related) or "청년" in compact):
        return False

    return True


def fetch(url: str) -> str | None:
    try:
        res = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        if res.status_code >= 400:
            return None
        if not res.encoding or res.encoding.lower() == "iso-8859-1":
            res.encoding = res.apparent_encoding or "utf-8"
        return res.text
    except Exception:
        return None


def extract_candidate_links(base_url: str, html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str]] = []

    for a in soup.find_all("a"):
        href = a.get("href") or ""
        title = " ".join(a.get_text(" ", strip=True).split())

        if not href or href.startswith("javascript:") or href.startswith("#"):
            continue

        full_url = urljoin(base_url, href)

        if not is_probably_url(full_url):
            continue

        joined = f"{title} {href}"

        if any(k in joined for k in INCLUDE_KEYWORDS + MENU_KEYWORDS):
            links.append((title or full_url, full_url))

    seen = set()
    unique: list[tuple[str, str]] = []

    for title, url in links:
        normalized = normalize_post_url(url)

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append((title, normalized))

    return unique[:30]


def same_domain_or_sub(base_url: str, target_url: str) -> bool:
    try:
        base_host = urlparse(base_url).netloc.replace("www.", "")
        target_host = urlparse(target_url).netloc.replace("www.", "")
        return target_host.endswith(base_host) or base_host.endswith(target_host)
    except Exception:
        return False


def make_post(center: Center, title: str, url: str, matched: str | None) -> RecruitPost:
    return RecruitPost(
        region=f"{center.region1} {center.region2}".strip(),
        center_name=center.center_name,
        operator_name=center.operator_name,
        title=title[:120],
        url=normalize_post_url(url),
        source="homepage",
        matched_keyword=matched,
    )


def make_title_key(post: RecruitPost) -> str:
    title = re.sub(r"\s+", "", post.title.lower())
    title = re.sub(r"\([^)]*\)", "", title)
    title = re.sub(r"\[[^\]]*\]", "", title)
    title = re.sub(r"photo|file|new|공지사항", "", title)
    return f"{post.center_name}:{title[:60]}"


def scan_center_homepage(center: Center) -> list[RecruitPost]:
    posts: list[RecruitPost] = []
    homepage = normalize_url(center.homepage_url)

    if not is_probably_url(homepage) or is_external_or_social(homepage):
        return posts

    html = fetch(homepage)

    if not html:
        return posts

    for title, url in extract_candidate_links(homepage, html):
        hit, matched = keyword_hit(title)

        if hit and is_likely_recruit_post(title, url):
            posts.append(make_post(center, title, url, matched))

    candidates = [
        x for x in extract_candidate_links(homepage, html)
        if same_domain_or_sub(homepage, x[1])
    ]

    for _, candidate_url in candidates[:8]:
        sub_html = fetch(candidate_url)

        if not sub_html:
            continue

        for title, url in extract_candidate_links(candidate_url, sub_html):
            hit, matched = keyword_hit(title)

            if hit and is_likely_recruit_post(title, url):
                posts.append(make_post(center, title, url, matched))

    unique = {}

    for post in posts:
        key = make_title_key(post)
        unique.setdefault(key, post)

    return list(unique.values())


def scan_centers(centers: list[Center], limit: int | None = None) -> list[RecruitPost]:
    results: list[RecruitPost] = []

    for center in centers[:limit] if limit else centers:
        results.extend(scan_center_homepage(center))

    return results
