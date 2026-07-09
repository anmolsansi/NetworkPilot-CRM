import logging
import re
from urllib.parse import urlparse

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
# Valid LinkedIn profile URL patterns
LINKEDIN_PROFILE_PATTERN = re.compile(r"^linkedin\.com/in/[a-zA-Z0-9_-]+/?$")

# Pages to reject (not profiles)
REJECTED_PATHS = [
    "/company/",
    "/jobs/",
    "/school/",
    "/feed/",
    "/search/",
    "/messaging/",
    "/notifications/",
    "/mynetwork/",
    "/notifications/",
    "/in/",
]


def normalize_linkedin_url(url: str) -> tuple[str, str] | None:
    """
    Normalize a LinkedIn profile URL and extract the slug.

    Returns:
        Tuple of (normalized_url, slug) or None if invalid.

    Examples:
        >>> normalize_linkedin_url("https://www.linkedin.com/in/abc/?utm_source=x")
        ("linkedin.com/in/abc", "abc")
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    hostname = parsed.hostname or ""

    # Normalize hostname
    if not hostname:
        return None

    hostname = hostname.lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    # Must be LinkedIn
    if hostname != "linkedin.com":
        return None

    path = parsed.path.rstrip("/")

    # Validate profile path format: /in/{slug}
    if not path.startswith("/in/"):
        return None

    match = LINKEDIN_PROFILE_PATTERN.match(hostname + path)
    if not match:
        return None

    # Extract slug (everything after /in/)
    slug = path[4:].strip("/")

    if not slug:
        return None

    # Normalize: lowercase slug
    normalized_url = f"linkedin.com/in/{slug.lower()}"

    return normalized_url, slug.lower()


def is_valid_linkedin_profile_url(url: str) -> bool:
    """Check if a URL is a valid LinkedIn profile URL."""
    return normalize_linkedin_url(url) is not None


def extract_linkedin_slug(url: str) -> str | None:
    """Extract just the slug from a LinkedIn profile URL."""
    result = normalize_linkedin_url(url)
    return result[1] if result else None
