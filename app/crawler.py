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
    """
    같은 게시글인데 검색 파라미터만 다른 URL을 최대한 같은 URL로 정리합니다.
    """
    try:
        parsed = urlparse(url)
        remove_keys = {
            "q", "field", "wrd", "search", "search_key", "keyword",
            "page", "offset", "sk", "sw", "category", "cate1",
            "search_first_subject", "list_mode", "auto_frame", "me_popup",
            "from", "fromNxList", "searchType", "placePath", "entry",
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
        "down.html",
        "download",
        "filedown",
        "file_down",
        "post_file_download",
        "bbsmsgfiledown",
        ".pdf",
        ".hwp",
        ".hwpx",
        ".png",
        ".jpg",
        ".jpeg",
    ])


def is_generic_menu_title(title: str) -> bool:
    compact = re.sub(r"\s+", "", title or "")
    return compact in {
        "채용공고", "공고", "공지", "공지사항", "알림", "소식",
        "새소식", "센터소식", "게시판", "열린마당"
    }


def keyword_hit(text: str) -> tuple[bool, str | None]:
    compact = re.sub(r"\s+", " ", text or "")
    for bad in EXCLUDE_KEYWORDS:
        if bad in compact:
            return False, None
    for good in INCLUDE_KEYWORDS:
        if good in compact:
            return True, good
    return False, None


def is_likely_recruit_post(title: str, url: str) -> bool:
    """
    실제 공고가 아닌 첨부파일, 메뉴, 후기, 일반 일자리 정보를 최대한 제외합니다.
    """
    if is_bad_url(url):
        return False

    if is_generic_menu_title(title):
        return False

    compact = re.sub(r"\s+", " ", title or "")

    # 제목에 채용 의미가 아예 없고 '팀장/센터장/정규직/기간제' 같은 단어만 잡힌 경우 제외
    recruit_signals = [
        "채용", "모집", "공고", "재공고", "직원", "근로자",
        "매니저", "코디", "전담인력", "청년지원매니저", "청년코디"
    ]
    if not any(signal in compact for signal in recruit_signals):
        return False

    # 후기/사업/정책성 문구 제외 보강
    bad_signals = [
        "후기", "감사합니다", "지원사업", "장려금", "학자금", "장학금",
        "취업 역량", "업무협약", "사업안내", "채용지원 모집중",
        "청년정규직 내일지원사업", "기간제·파견근로자 출산전후휴가",
    ]
    if any(bad in compact for bad in bad_signals):
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
        key = normalized

        if key in seen:
            continue

        seen.add(key)
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
        key = normalize_post_url(post.url)
        unique.setdefault(key, post)

    return list(unique.values())


def scan_centers(centers: list[Center], limit: int | None = None) -> list[RecruitPost]:
    results: list[RecruitPost] = []

    for center in centers[:limit] if limit else centers:
        results.extend(scan_center_homepage(center))

    return results
