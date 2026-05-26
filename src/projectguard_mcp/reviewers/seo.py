from __future__ import annotations

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings


def review_seo(public_pages: dict[str, str]) -> dict:
    findings: list[Finding] = []

    if not public_pages:
        findings.append(Finding("NO_PUBLIC_PAGES", "medium", "No public page HTML was provided for SEO review."))

    for path, html in public_pages.items():
        h = html.lower()
        if "<title" not in h:
            findings.append(Finding("MISSING_TITLE", "medium", "Page is missing <title>.", path=path))
        if "name=\"description\"" not in h and "name='description'" not in h:
            findings.append(Finding("MISSING_META_DESCRIPTION", "medium", "Page is missing meta description.", path=path))
        if "rel=\"canonical\"" not in h and "rel='canonical'" not in h:
            findings.append(Finding("MISSING_CANONICAL", "low", "Page is missing canonical link.", path=path))
        if "og:title" not in h:
            findings.append(Finding("MISSING_OG_TAGS", "low", "Page is missing OpenGraph tags.", path=path))
        if "<h1" not in h:
            findings.append(Finding("MISSING_H1", "medium", "Page is missing one clear H1.", path=path))
        if "privacy" not in h and "terms" not in h and path in {"/", "index.html", "home"}:
            findings.append(Finding("MISSING_LEGAL_FOOTER_LINKS", "low", "Homepage/footer does not show privacy/terms links.", path=path))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="SEO basics passed." if score >= 85 else "SEO basics need fixes.",
        metadata={"page_count": len(public_pages)},
    ).to_dict()
