from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from projectguard_mcp.reviewers.anti_slop import review_project_text
from projectguard_mcp.reviewers.code_quality import review_code_quality
from projectguard_mcp.reviewers.file_plan import review_file_plan
from projectguard_mcp.scoring import final_project_score


def _read_files(paths: list[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for item in paths:
        path = Path(item)
        if path.is_file():
            data[str(path)] = path.read_text(encoding="utf-8", errors="replace")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ProjectGuard local checks.")
    parser.add_argument("--project-type", default="web app")
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--text", default="")
    args = parser.parse_args(argv)

    files = _read_files(args.files)
    results = {
        "file_plan": review_file_plan(args.project_type, list(files.keys())),
        "code_quality": review_code_quality(files),
        "text": review_project_text(args.text) if args.text else None,
    }
    ux_score = 85
    seo_score = 100
    results["final"] = final_project_score(
        code_score=results["code_quality"]["score"],
        ux_score=ux_score,
        security_score=85,
        seo_score=seo_score,
    )
    print(json.dumps(results, indent=2))
    return 0 if results["final"]["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
