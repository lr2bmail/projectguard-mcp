from projectguard_mcp.reviewers.seo import review_seo

GOOD_HTML = """<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>A Good Page Title That Is The Right Length</title>
    <meta name="description" content="This is a well-written meta description that provides enough detail for search engine results pages.">
    <link rel="canonical" href="https://example.com/">
    <meta property="og:title" content="A Good Page Title">
    <meta property="og:description" content="A good description">
    <meta property="og:image" content="https://example.com/img.png">
    <meta property="og:url" content="https://example.com/">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <script type="application/ld+json">{"@type":"Organization"}</script>
</head>
<body>
    <h1>Main Heading</h1>
    <p>This page has enough content to not be flagged as thin content. It describes a product
    or service with meaningful information that would be useful for visitors and search engines.
    The content is detailed and specific.</p>
    <img src="photo.jpg" alt="A descriptive alt text" width="800" height="600">
    <a href="/privacy">Privacy</a> <a href="/terms">Terms</a>
</body>
</html>"""


def test_missing_title_flagged():
    html = "<html><head></head><body></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "MISSING_TITLE" in codes


def test_title_too_short_flagged():
    html = "<html><head><title>Hi</title></head><body></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "TITLE_LENGTH_ISSUE" in codes


def test_meta_description_too_short_flagged():
    html = '<html><head><title>Test Page</title><meta name="description" content="Short"></head><body></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "META_DESCRIPTION_LENGTH" in codes


def test_multiple_h1_flagged():
    html = "<html><body><h1>First</h1><h1>Second</h1></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "MULTIPLE_H1" in codes


def test_heading_hierarchy_skip_flagged():
    html = "<html><body><h1>Main</h1><h3>Skip</h3></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "HEADING_HIERARCHY_SKIP" in codes


def test_missing_viewport_flagged():
    html = "<html><head><title>Test</title></head><body></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "MISSING_VIEWPORT" in codes


def test_missing_lang_attr_flagged():
    html = "<html><head><title>Test</title></head><body></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "MISSING_LANG_ATTR" in codes


def test_noindex_trap_flagged():
    html = '<html><head><meta name="robots" content="noindex, nofollow"></head><body></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "NOINDEX_TRAP" in codes


def test_image_missing_alt_flagged():
    html = '<html><body><img src="photo.jpg"></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "IMAGE_MISSING_ALT" in codes


def test_missing_structured_data_flagged():
    html = "<html><head><title>Test</title></head><body></body></html>"
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "MISSING_STRUCTURED_DATA" in codes


def test_deprecated_schema_flagged():
    html = '<html><head><script type="application/ld+json">{"@type":"HowTo"}</script></head><body></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "DEPRECATED_SCHEMA_TYPE" in codes


def test_clean_page_passes():
    result = review_seo({"index.html": GOOD_HTML})
    assert result["score"] >= 85
