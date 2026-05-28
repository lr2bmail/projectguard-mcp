from __future__ import annotations

import re

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings

DOCKER_PATH_MARKERS = ["dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
DANGEROUS_CAPABILITIES = ["sys_admin", "sys_ptrace", "net_admin", "sys_module"]
SECRET_ENV_PATTERNS = [
    r"ENV\s+.*(SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)=",
    r"environment:\s*(?:\n|.)*(SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)",
]


def _docker_files(files: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path, content in files.items():
        normalized = path.lower().replace("\\", "/")
        name = normalized.rsplit("/", 1)[-1]
        if name in DOCKER_PATH_MARKERS or normalized.startswith("docker/"):
            result[path] = content
    return result


def _has_file(files: dict[str, str], wanted: str) -> bool:
    return any(path.lower().replace("\\", "/").endswith(wanted) for path in files)


def review_docker_security(files: dict[str, str] | None = None) -> dict:
    """Review Dockerfile and docker-compose hardening issues."""
    files = files or {}
    findings: list[Finding] = []
    docker_files = _docker_files(files)

    if not docker_files:
        findings.append(Finding(
            code="NO_DOCKER_FILES_DETECTED",
            severity="info",
            message="No Dockerfile or Compose file was detected.",
            recommendation="Run this review when the project includes Docker deployment files.",
        ))

    for path, content in docker_files.items():
        lowered = content.lower()
        name = path.lower().replace("\\", "/").rsplit("/", 1)[-1]

        if name == "dockerfile" or path.lower().endswith("dockerfile"):
            if re.search(r"^\s*from\s+[^\n:]+:latest\b", content, re.I | re.M):
                findings.append(Finding(
                    code="DOCKER_BASE_IMAGE_LATEST",
                    severity="medium",
                    message="Dockerfile uses a latest tag for the base image.",
                    recommendation="Pin a specific base image version and keep it updated intentionally.",
                    path=path,
                ))

            if not re.search(r"^\s*user\s+", content, re.I | re.M):
                findings.append(Finding(
                    code="DOCKER_RUNS_AS_ROOT",
                    severity="high",
                    message="Dockerfile does not set a non-root USER.",
                    recommendation="Create and switch to a non-root user before running the app.",
                    path=path,
                ))

            if "healthcheck" not in lowered:
                findings.append(Finding(
                    code="DOCKER_MISSING_HEALTHCHECK",
                    severity="low",
                    message="Dockerfile has no HEALTHCHECK.",
                    recommendation="Add a lightweight healthcheck for production containers.",
                    path=path,
                ))

            if re.search(r"^\s*add\s+https?://", content, re.I | re.M):
                findings.append(Finding(
                    code="DOCKER_REMOTE_ADD",
                    severity="medium",
                    message="Dockerfile uses ADD with a remote URL.",
                    recommendation="Use curl/wget with checksum verification or vendor trusted artifacts.",
                    path=path,
                ))

        if "privileged: true" in lowered:
            findings.append(Finding(
                code="DOCKER_PRIVILEGED_CONTAINER",
                severity="critical",
                message="Compose file enables privileged container mode.",
                recommendation="Remove privileged mode and grant only the exact capability required, if any.",
                path=path,
            ))

        if "network_mode: host" in lowered or "network: host" in lowered:
            findings.append(Finding(
                code="DOCKER_HOST_NETWORK",
                severity="high",
                message="Container uses host networking.",
                recommendation="Use isolated bridge networks and expose only required ports.",
                path=path,
            ))

        if "pid: host" in lowered:
            findings.append(Finding(
                code="DOCKER_HOST_PID",
                severity="high",
                message="Container uses host PID namespace.",
                recommendation="Avoid host PID namespace unless strictly required and reviewed.",
                path=path,
            ))

        if "/var/run/docker.sock" in lowered:
            findings.append(Finding(
                code="DOCKER_SOCKET_MOUNTED",
                severity="critical",
                message="Docker socket is mounted into a container.",
                recommendation="Do not mount the Docker socket; it effectively grants host-level control.",
                path=path,
            ))

        if any(cap in lowered for cap in DANGEROUS_CAPABILITIES):
            findings.append(Finding(
                code="DOCKER_DANGEROUS_CAPABILITY",
                severity="high",
                message="Dangerous Linux capability is granted to the container.",
                recommendation="Remove broad capabilities such as SYS_ADMIN, SYS_PTRACE, NET_ADMIN, or SYS_MODULE.",
                path=path,
            ))

        if any(re.search(pattern, content, re.I) for pattern in SECRET_ENV_PATTERNS):
            findings.append(Finding(
                code="DOCKER_SECRET_IN_ENV",
                severity="critical",
                message="Possible secret is stored directly in Docker ENV or Compose environment.",
                recommendation="Use runtime secrets or environment injection outside source control.",
                path=path,
            ))

    if docker_files and not _has_file(files, ".dockerignore"):
        findings.append(Finding(
            code="DOCKERIGNORE_MISSING",
            severity="medium",
            message="Docker deployment files exist but .dockerignore is missing.",
            recommendation="Add .dockerignore to avoid copying secrets, caches, node_modules, .venv, and git history.",
        ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="Docker security review passed." if score >= 85 else "Docker security review found issues to fix.",
        metadata={
            "docker_file_count": len(docker_files),
            "frameworks": ["CIS Docker Benchmark", "container hardening"],
        },
    ).to_dict()
