from urllib.parse import urlparse

from scraper.config import BASE_URL


def extract_url_from_post(post: dict) -> str | None:
    for key in ("url", "permalink"):
        val = post.get(key)
        if val and val.startswith("http"):
            return val
    slug = post.get("slug")
    if slug:
        return f"{BASE_URL}/{slug}"
    return None


def derive_slug(url: str) -> str:
    parts = [p for p in urlparse(url).path.split("/") if p]
    return parts[-1] if parts else "unknown"
