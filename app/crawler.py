from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from .config import INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS, MENU_KEYWORDS, REQUEST_TIMEOUT, USER_AGENT
from .models import Center, RecruitPost


def is_probably_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def normalize_url(url: str) -> str:
    return url.strip()


def is_external_or_social(url: str) -> bool:
    lowered = url.lower()
    return any(x in lowered for x in [
        "instagram.com", "facebook.com", "youtube.com", "map.naver.com", "naver.me",
        "pf.kakao.com", "kakaotalk", "blog.naver.com"
    ])


def keyword_hit(text: str) -> tuple[bool, str | None]:
    compact = re.sub(r"\s+", " ", text or "")
    for bad in EXCLUDE_KEYWORDS:
        if bad in compact:
            return False, None
    for good in INCLUDE_KEYWORDS:
        if good in compact:
            return True, good
    return False, None


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
    # 중복 제거
    seen = set()
    unique: list[tuple[str, str]] = []
    for title, url in links:
        if url in seen:
            continue
        seen.add(url)
        unique.append((title, url))
    return unique[:30]


def same_domain_or_sub(base_url: str, target_url: str) -> bool:
    try:
        base_host = urlparse(base_url).netloc.replace("www.", "")
        target_host = urlparse(target_url).netloc.replace("www.", "")
        return target_host.endswith(base_host) or base_host.endswith(target_host)
    except Exception:
        return False


def scan_center_homepage(center: Center) -> list[RecruitPost]:
    posts: list[RecruitPost] = []
    homepage = normalize_url(center.homepage_url)
    if not is_probably_url(homepage) or is_external_or_social(homepage):
        return posts

    html = fetch(homepage)
    if not html:
        return posts

    # 1) 메인 페이지 링크 텍스트 자체에서 채용 키워드 탐색
    for title, url in extract_candidate_links(homepage, html):
        hit, matched = keyword_hit(title)
        if hit:
            posts.append(RecruitPost(
                region=f"{center.region1} {center.region2}".strip(),
                center_name=center.center_name,
                operator_name=center.operator_name,
                title=title[:120],
                url=url,
                source="homepage",
                matched_keyword=matched,
            ))

    # 2) 공지/채용/게시판 후보 페이지에 들어가서 다시 링크 탐색
    candidates = [x for x in extract_candidate_links(homepage, html) if same_domain_or_sub(homepage, x[1])]
    for _, candidate_url in candidates[:8]:
        sub_html = fetch(candidate_url)
        if not sub_html:
            continue
        for title, url in extract_candidate_links(candidate_url, sub_html):
            hit, matched = keyword_hit(title)
            if hit:
                posts.append(RecruitPost(
                    region=f"{center.region1} {center.region2}".strip(),
                    center_name=center.center_name,
                    operator_name=center.operator_name,
                    title=title[:120],
                    url=url,
                    source="homepage",
                    matched_keyword=matched,
                ))
    # URL 기준 중복 제거
    unique = {}
    for post in posts:
        unique.setdefault(post.url, post)
    return list(unique.values())


def scan_centers(centers: list[Center], limit: int | None = None) -> list[RecruitPost]:
    results: list[RecruitPost] = []
    for center in centers[:limit] if limit else centers:
        results.extend(scan_center_homepage(center))
    return results
