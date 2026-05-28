from __future__ import annotations

import re

from projectguard_mcp.config import (
    DEFAULT_PAGE_WORD_COUNT,
    DEPRECATED_SCHEMA_TYPES,
    PAGE_WORD_COUNT_MINIMUMS,
    SEO_META_DESC_MAX_LENGTH,
    SEO_META_DESC_MIN_LENGTH,
    SEO_TITLE_MAX_LENGTH,
    SEO_TITLE_MIN_LENGTH,
)
from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import count_words, strip_html_tags


def _detect_page_type(path: str) -> str:
    lowered = path.lower().replace("\\", "/")
    if "blog" in lowered or "post" in lowered or "article" in lowered:
        return "blog"
    if "product" in lowered or "shop" in lowered or "item" in lowered:
        return "product"
    if "service" in lowered:
        return "service"
    return "homepage"


def _check_page_seo(path: str, html: str, findings: list[Finding]) -> None:
    h = html.lower()

    # -- Title tag --
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not title_match:
        findings.append(Finding("MISSING_TITLE", "medium", "Page is missing <title>.", path=path))
    else:
        title_text = title_match.group(1).strip()
        title_len = len(title_text)
        if title_len < SEO_TITLE_MIN_LENGTH or title_len > SEO_TITLE_MAX_LENGTH:
            findings.append(Finding(
                "TITLE_LENGTH_ISSUE", "medium",
                f"Page title is {title_len} characters (recommended {SEO_TITLE_MIN_LENGTH}-{SEO_TITLE_MAX_LENGTH}).",
                recommendation="Keep page titles between 30-70 characters for optimal display in search results.",
                path=path,
            ))

    # -- Meta description --
    meta_match = re.search(
        r'<meta[^>]+name\s*=\s*["\']?description["\']?[^>]+content\s*=\s*["\']([^"\']*)["\']',
        h,
    ) or re.search(
        r'<meta[^>]+content\s*=\s*["\']([^"\']*)["\'][^>]+name\s*=\s*["\']?description["\']?',
        h,
    )
    if not meta_match:
        findings.append(Finding("MISSING_META_DESCRIPTION", "medium", "Page is missing meta description.", path=path))
    else:
        desc_len = len(meta_match.group(1).strip())
        if desc_len < SEO_META_DESC_MIN_LENGTH or desc_len > SEO_META_DESC_MAX_LENGTH:
            findings.append(Finding(
                "META_DESCRIPTION_LENGTH", "medium",
                f"Meta description is {desc_len} characters (recommended {SEO_META_DESC_MIN_LENGTH}-{SEO_META_DESC_MAX_LENGTH}).",
                recommendation="Keep meta descriptions between 100-170 characters.",
                path=path,
            ))

    # -- Canonical --
    canonical_matches = re.findall(r'rel\s*=\s*["\']canonical["\']', h)
    if not canonical_matches:
        findings.append(Finding("MISSING_CANONICAL", "low", "Page is missing canonical link.", path=path))
    else:
        if len(canonical_matches) > 1:
            findings.append(Finding("MULTIPLE_CANONICAL", "high", "Page has multiple canonical tags.", path=path))
        canonical_href = re.search(r'<link[^>]+rel\s*=\s*["\']canonical["\'][^>]+href\s*=\s*["\']([^"\']*)["\']', h)
        if canonical_href and not canonical_href.group(1).startswith("https://"):
            findings.append(Finding("CANONICAL_NOT_HTTPS", "medium", "Canonical URL is not HTTPS.", path=path))

    # -- Open Graph --
    if "og:title" not in h:
        findings.append(Finding("MISSING_OG_TAGS", "low", "Page is missing OpenGraph tags.", path=path))
    elif any(tag not in h for tag in ["og:image", "og:url", "og:type", "og:description"]):
        missing = [tag for tag in ["og:image", "og:url", "og:type", "og:description"] if tag not in h]
        findings.append(Finding(
            "INCOMPLETE_OG_TAGS", "low",
            f"Page is missing OG tags: {', '.join(missing)}.",
            recommendation="Include og:title, og:description, og:image, og:url, and og:type for rich social sharing.",
            path=path,
        ))

    # -- Twitter Card --
    if "twitter:card" not in h:
        findings.append(Finding("MISSING_TWITTER_CARD", "low", "Page is missing Twitter Card meta tags.", path=path))

    # -- H1 --
    h1_matches = re.findall(r"<h1[\s>]", h)
    if not h1_matches:
        findings.append(Finding("MISSING_H1", "medium", "Page is missing one clear H1.", path=path))
    elif len(h1_matches) > 1:
        findings.append(Finding("MULTIPLE_H1", "medium", f"Page has {len(h1_matches)} H1 tags (should be exactly one).", path=path))

    # -- Heading hierarchy --
    headings = re.findall(r"<(h[1-6])[\s>]", h)
    if headings:
        levels = [int(hd[1]) for hd in headings]
        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] > 1:
                findings.append(Finding(
                    "HEADING_HIERARCHY_SKIP", "low",
                    f"Heading hierarchy skip: <{headings[i-1]}> followed by <{headings[i]}>.",
                    recommendation="Do not skip heading levels. Maintain a logical hierarchy.",
                    path=path,
                ))
                break

    # -- Viewport --
    if 'name="viewport"' not in h and "name='viewport'" not in h:
        findings.append(Finding("MISSING_VIEWPORT", "medium", "Page is missing viewport meta tag.", path=path))

    # -- HTML lang --
    if "<html" in h and not re.search(r"<html[^>]+lang\s*=", h):
        findings.append(Finding("MISSING_LANG_ATTR", "low", "Page is missing lang attribute on <html>.", path=path))

    # -- Meta robots noindex trap --
    if re.search(r'name\s*=\s*["\']robots["\'].*content\s*=\s*["\'][^"\']*noindex', h):
        findings.append(Finding(
            "NOINDEX_TRAP", "high",
            "Page has noindex directive, preventing search engine indexing.",
            recommendation="Remove noindex unless intentionally hiding the page from search engines.",
            path=path,
        ))

    # -- Image alt text --
    img_tags = re.findall(r"<img[^>]*>", h)
    for img in img_tags:
        if "alt=" not in img:
            findings.append(Finding(
                "IMAGE_MISSING_ALT", "medium",
                "Image tag missing alt attribute.",
                recommendation="Add descriptive alt text to all images for accessibility and image search.",
                path=path,
            ))
            break
        alt_match = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', img)
        if alt_match:
            alt_text = alt_match.group(1).strip().lower()
            if not alt_text or re.match(r"^(image|photo|picture|img)\.\w+$", alt_text):
                findings.append(Finding(
                    "IMAGE_MISSING_ALT", "medium",
                    "Image has generic or empty alt text.",
                    recommendation="Use descriptive alt text that explains the image content.",
                    path=path,
                ))
                break

    # -- Image dimensions --
    for img in img_tags:
        if "width=" not in img or "height=" not in img:
            findings.append(Finding(
                "IMAGE_MISSING_DIMENSIONS", "low",
                "Image tag missing width/height attributes.",
                recommendation="Add width and height attributes to prevent layout shift (CLS).",
                path=path,
            ))
            break

    # -- JSON-LD structured data --
    jsonld_scripts = re.findall(r'<script[^>]+type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S)
    if not jsonld_scripts:
        findings.append(Finding(
            "MISSING_STRUCTURED_DATA", "low",
            "Page is missing JSON-LD structured data.",
            recommendation="Add JSON-LD structured data for rich search results.",
            path=path,
        ))
    else:
        for script in jsonld_scripts:
            for deprecated in DEPRECATED_SCHEMA_TYPES:
                if re.search(rf'"@type"\s*:\s*"?{deprecated}"?', script):
                    findings.append(Finding(
                        "DEPRECATED_SCHEMA_TYPE", "medium",
                        f"Deprecated schema type detected: {deprecated}.",
                        recommendation="Remove deprecated schema types that may cause search engine warnings.",
                        path=path,
                    ))

    # -- Content word count --
    visible_text = strip_html_tags(html)
    word_count = count_words(visible_text)
    page_type = _detect_page_type(path)
    minimum = PAGE_WORD_COUNT_MINIMUMS.get(page_type, DEFAULT_PAGE_WORD_COUNT)
    if word_count < minimum:
        findings.append(Finding(
            "THIN_CONTENT", "medium",
            f"Page has ~{word_count} words (recommended {minimum}+ for {page_type} pages).",
            recommendation="Increase content depth for this page type to meet SEO minimums.",
            path=path,
        ))


def _check_site_wide_seo(pages: dict[str, str], findings: list[Finding]) -> None:
    """Checks that require multiple pages (sitemap, robots.txt, internal linking, etc.)."""
    all_paths = {p.lower().replace("\\", "/") for p in pages}
    all_html_lower = "\n".join(pages.values()).lower()

    # -- MISSING_SITEMAP_XML --
    has_sitemap = any("sitemap" in p for p in all_paths) or "</urlset>" in all_html_lower
    if not has_sitemap and len(pages) >= 2:
        findings.append(Finding(
            "MISSING_SITEMAP_XML", "high",
            "No sitemap.xml detected among the provided pages.",
            recommendation="Add a sitemap.xml listing all public URLs and submit it to Google Search Console.",
        ))

    # -- MISSING_ROBOTS_TXT --
    has_robots = any(p.endswith("robots.txt") for p in all_paths) or "user-agent:" in all_html_lower
    if not has_robots and len(pages) >= 2:
        findings.append(Finding(
            "MISSING_ROBOTS_TXT", "high",
            "No robots.txt detected among the provided pages.",
            recommendation="Add a robots.txt file that allows search engine crawling and points to the sitemap.",
        ))

    # -- COMPRESSION_NOT_ENABLED --
    # Check for server config files or HTML hints of compression
    compression_hints = [
        "content-encoding", "gzip", "deflate", "brotli", "br",
        "compress=true", "compression", "enable_gzip",
    ]
    if not any(hint in all_html_lower for hint in compression_hints) and len(pages) >= 2:
        findings.append(Finding(
            "COMPRESSION_NOT_ENABLED", "medium",
            "No visible compression headers or configuration detected.",
            recommendation="Enable gzip/brotli compression on the server for HTML, CSS, and JS files.",
        ))

    # -- STATIC_CACHE_HEADERS_MISSING --
    cache_hints = [
        "cache-control", "max-age", "etag", "expires", "stale-while-revalidate",
        "s-maxage", "immutable",
    ]
    has_cache_headers = any(hint in all_html_lower for hint in cache_hints)
    if not has_cache_headers and len(pages) >= 2:
        findings.append(Finding(
            "STATIC_CACHE_HEADERS_MISSING", "medium",
            "No visible cache headers for static assets.",
            recommendation="Set Cache-Control headers with max-age for CSS, JS, images, and fonts.",
        ))

    # -- CANONICAL_MISMATCH --
    # Check that canonical URLs match the actual page URL/path
    canonical_map: dict[str, str] = {}
    for path, html in pages.items():
        h = html.lower()
        canonical_href = re.search(
            r'<link[^>]+rel\s*=\s*["\']canonical["\'][^>]+href\s*=\s*["\']([^"\']*)["\']', h,
        )
        if canonical_href:
            canonical_map[path] = canonical_href.group(1)

    if len(canonical_map) >= 2:
        seen_targets: dict[str, list[str]] = {}
        for path, canonical in canonical_map.items():
            # Strip trailing slash for comparison
            normalized = canonical.rstrip("/")
            seen_targets.setdefault(normalized, []).append(path)
        for target, sources in seen_targets.items():
            if len(sources) > 1:
                findings.append(Finding(
                    "CANONICAL_MISMATCH", "high",
                    f"Multiple pages point to the same canonical URL: {target} (from {', '.join(sources)}).",
                    recommendation="Each page should have a unique canonical URL pointing to itself.",
                ))
                break

    # -- GENERIC_OG_IMAGE --
    og_images: list[str] = []
    for html in pages.values():
        h = html.lower()
        og_img = re.search(r'property\s*=\s*["\']og:image["\'][^>]+content\s*=\s*["\']([^"\']*)["\']', h)
        if not og_img:
            og_img = re.search(r'content\s*=\s*["\']([^"\']*)["\'][^>]+property\s*=\s*["\']og:image["\']', h)
        if og_img:
            og_images.append(og_img.group(1))
    if len(og_images) >= 3:
        unique_images = set(og_images)
        if len(unique_images) == 1:
            findings.append(Finding(
                "GENERIC_OG_IMAGE", "medium",
                "All pages share the same og:image, reducing social sharing click-through.",
                recommendation="Use unique og:image for each page reflecting its specific content.",
            ))

    # -- INTERNAL_LINKING_WEAK --
    for path, html in pages.items():
        h = html.lower()
        internal_links = re.findall(r'href\s*=\s*["\'](/[^"\']*)["\']', h)
        if len(pages) >= 3 and len(internal_links) < 2:
            findings.append(Finding(
                "INTERNAL_LINKING_WEAK", "medium",
                f"Page has only {len(internal_links)} internal links (recommend 3+ for sites with multiple pages).",
                recommendation="Add contextual internal links to related pages for better crawlability and user navigation.",
                path=path,
            ))

    # -- MISSING_BREADCRUMB_SCHEMA --
    has_breadcrumb = False
    for html in pages.values():
        jsonld_scripts = re.findall(
            r'<script[^>]+type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S,
        )
        for script in jsonld_scripts:
            if "breadcrumb" in script.lower():
                has_breadcrumb = True
                break
        if has_breadcrumb:
            break
    if not has_breadcrumb and len(pages) >= 3:
        findings.append(Finding(
            "MISSING_BREADCRUMB_SCHEMA", "low",
            "No BreadcrumbList structured data detected on any page.",
            recommendation="Add BreadcrumbList JSON-LD to help search engines understand site hierarchy.",
        ))


def review_seo(public_pages: dict[str, str]) -> dict:
    findings: list[Finding] = []

    if not public_pages:
        findings.append(Finding("NO_PUBLIC_PAGES", "medium", "No public page HTML was provided for SEO review."))
        score = score_from_findings(findings)
        return ReviewResult(
            approved=approval_from_score(score, 85),
            score=score,
            findings=findings,
            summary="No pages provided for SEO review.",
            metadata={"page_count": 0},
        ).to_dict()

    # Detect non-HTML input (description strings, URLs, etc.)
    non_html_pages: list[str] = []
    for path, html in public_pages.items():
        stripped = html.strip()
        if stripped and not stripped.startswith("<") and "<html" not in stripped.lower() and "<head" not in stripped.lower():
            non_html_pages.append(path)

    if non_html_pages:
        findings.append(Finding(
            "INPUT_NOT_HTML",
            severity="critical",
            message=(
                f"SEO review requires full rendered HTML, but {len(non_html_pages)} page(s) do not appear to be HTML: "
                f"{', '.join(non_html_pages[:5])}. "
                "Pass the complete HTML source of each page (including <head>, <body>, meta tags, etc.), "
                "not descriptions, URLs, or plain text."
            ),
            recommendation=(
                "Provide the actual rendered HTML of each page. "
                "In Flask/Django, use render_template_string() or fetch the page source from a running server. "
                "In Next.js, view page source in the browser. "
                "Each value must start with <html> or <!DOCTYPE html>."
            ),
        ))
        score = score_from_findings(findings)
        return ReviewResult(
            approved=False,
            score=score,
            findings=findings,
            summary="SEO review received non-HTML input. Pass full rendered HTML for accurate results.",
            metadata={"page_count": len(public_pages), "non_html_count": len(non_html_pages)},
        ).to_dict()

    for path, html in public_pages.items():
        _check_page_seo(path, html, findings)

        h = html.lower()
        if "privacy" not in h and "terms" not in h and path in {"/", "index.html", "home"}:
            findings.append(Finding("MISSING_LEGAL_FOOTER_LINKS", "low", "Homepage/footer does not show privacy/terms links.", path=path))

    _check_site_wide_seo(public_pages, findings)

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="SEO basics passed." if score >= 85 else "SEO basics need fixes.",
        metadata={"page_count": len(public_pages)},
    ).to_dict()
