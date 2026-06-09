from pathlib import Path
from .config import STATE_PATH


def load_sent_urls(path: Path = STATE_PATH) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def save_sent_urls(urls: set[str], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(urls)), encoding="utf-8")


def filter_new(posts):
    sent = load_sent_urls()
    new_posts = [p for p in posts if p.url not in sent]
    for p in new_posts:
        sent.add(p.url)
    save_sent_urls(sent)
    return new_posts
