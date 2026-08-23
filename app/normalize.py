import re
import unicodedata


_FEATURE_RE = re.compile(
    r"\s*[\(\[]?\s*(feat\.?|ft\.?|featuring|with)\s+.+$",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(
    r"\s*[\(\[][^)\]]*(remaster(?:ed)?|remix|edit|version|mix|deluxe|explicit|clean|radio)[^)\]]*[\)\]]",
    re.IGNORECASE,
)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_text(value: str) -> str:
    """Lowercase, strip accents/punctuation, drop common fluff for matching."""
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = _FEATURE_RE.sub("", text)
    text = _VERSION_RE.sub("", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    return " ".join(text.split())


def clean_title(value: str) -> str:
    """Strip feat/version tags but keep casing and punctuation (for slugifying)."""
    text = _FEATURE_RE.sub("", value or "")
    text = _VERSION_RE.sub("", text)
    return text.strip()


def cache_key(artist: str, title: str) -> str:
    return f"{normalize_text(artist)}|{normalize_text(title)}"


def slugify(value: str, *, keep_punctuation: str = "") -> str:
    """Approximate WhoSampled URL slug style.

    WhoSampled keeps some trailing punctuation in paths (e.g. Stop! → /Stop!/).
    Pass keep_punctuation='!?' when guessing track slugs.
    """
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.strip()
    text = re.sub(r"['’]", "", text)
    allowed = re.escape(keep_punctuation)
    pattern = rf"[^A-Za-z0-9{allowed}]+" if allowed else r"[^A-Za-z0-9]+"
    text = re.sub(pattern, "-", text)
    return text.strip("-")


def track_slug_candidates(title: str) -> list[str]:
    """Direct-URL guesses: punctuation-preserving first, then stripped."""
    seen: set[str] = set()
    candidates: list[str] = []
    for keep in ("!?", ""):
        slug = slugify(title, keep_punctuation=keep)
        if slug and slug not in seen:
            seen.add(slug)
            candidates.append(slug)
    # Also try appending ! when the title has no punctuation (Donuts-style titles)
    if title and not title.rstrip().endswith(("!", "?")):
        with_bang = slugify(title + "!", keep_punctuation="!?")
        if with_bang and with_bang not in seen:
            candidates.append(with_bang)
    return candidates
