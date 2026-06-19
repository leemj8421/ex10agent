"""코드 소스 취득 유틸리티 - GitHub URL, 웹페이지, 직접 입력 처리"""
import os
import re
import httpx
from bs4 import BeautifulSoup
from github import Github, Auth


def detect_language(code: str, filename: str = "") -> str:
    """파일명 또는 코드 내용으로 언어 감지"""
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "JavaScript(React)", ".tsx": "TypeScript(React)",
        ".java": "Java", ".go": "Go", ".rs": "Rust",
        ".cpp": "C++", ".c": "C", ".cs": "C#",
        ".php": "PHP", ".rb": "Ruby", ".kt": "Kotlin",
        ".swift": "Swift", ".sh": "Shell", ".sql": "SQL",
        ".html": "HTML", ".css": "CSS",
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang

    # 코드 내용 기반 휴리스틱
    if "def " in code and "import " in code:
        return "Python"
    if "function " in code or "const " in code or "let " in code:
        return "JavaScript"
    if "public class " in code or "System.out" in code:
        return "Java"
    if "package main" in code or "func " in code:
        return "Go"
    return "Unknown"


def parse_github_url(url: str) -> dict:
    """GitHub URL 파싱 - PR, 파일, 레포지토리 구분"""
    url = url.strip()
    
    # PR URL: github.com/owner/repo/pull/123
    pr_match = re.match(
        r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$", url
    )
    if pr_match:
        return {
            "type": "pr",
            "owner": pr_match.group(1),
            "repo": pr_match.group(2),
            "number": int(pr_match.group(3)),
        }

    # 파일 URL: github.com/owner/repo/blob/branch/path
    file_match = re.match(
        r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$", url
    )
    if file_match:
        return {
            "type": "file",
            "owner": file_match.group(1),
            "repo": file_match.group(2),
            "branch": file_match.group(3),
            "path": file_match.group(4),
        }

    # Raw URL
    raw_match = re.match(r"^https?://raw\.githubusercontent\.com/(.+)$", url)
    if raw_match:
        return {"type": "raw", "url": url}

    # 레포지토리 URL (경로 없음)
    repo_match = re.match(r"^https?://github\.com/([^/]+)/([^/?#]+)/?$", url)
    if repo_match:
        return {
            "type": "repo",
            "owner": repo_match.group(1),
            "repo": repo_match.group(2).rstrip(".git"),
        }

    # 파일 다이렉트 URL (blob 분기가 없는 형태) e.g., github.com/owner/repo/main.py
    direct_file_match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/(.+)$", url)
    if direct_file_match:
        return {
            "type": "file_direct",
            "owner": direct_file_match.group(1),
            "repo": direct_file_match.group(2),
            "path": direct_file_match.group(3),
        }

    return {"type": "unknown"}


async def fetch_github_code(url: str) -> dict:
    """GitHub에서 코드 가져오기"""
    raw_token = os.getenv("GITHUB_TOKEN", "")
    # 플레이스홀더 값이면 무시하고 비인증 모드 사용
    token = raw_token if raw_token and not raw_token.startswith("your_") and raw_token != "ghp_" else None
    parsed = parse_github_url(url)

    if parsed["type"] == "raw":
        async with httpx.AsyncClient() as client:
            resp = await client.get(parsed["url"])
            return {"code": resp.text, "filename": url.split("/")[-1], "source": url}

    auth = Auth.Token(token) if token else None
    g = Github(auth=auth)

    if parsed["type"] == "pr":
        repo = g.get_repo(f"{parsed['owner']}/{parsed['repo']}")
        pr = repo.get_pull(parsed["number"])
        files = list(pr.get_files())
        # 코드 파일만 수집 (최대 5개)
        code_files = [
            f for f in files
            if f.filename.endswith(
                (".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".cs")
            )
        ][:5]

        combined = []
        for f in code_files:
            if f.patch:
                combined.append(f"# File: {f.filename}\n{f.patch}")
        code = "\n\n".join(combined) if combined else "변경된 코드 파일을 찾을 수 없습니다."
        return {
            "code": code,
            "filename": f"PR #{parsed['number']}",
            "source": url,
            "pr_title": pr.title,
            "files": [f.filename for f in code_files],
        }

    if parsed["type"] == "file":
        repo = g.get_repo(f"{parsed['owner']}/{parsed['repo']}")
        content = repo.get_contents(parsed["path"], ref=parsed["branch"])
        code = content.decoded_content.decode("utf-8")
        return {"code": code, "filename": parsed["path"], "source": url}

    if parsed["type"] == "repo":
        # README + 주요 파일 목록 반환
        repo = g.get_repo(f"{parsed['owner']}/{parsed['repo']}")
        try:
            readme = repo.get_readme()
            code = readme.decoded_content.decode("utf-8")[:3000]
        except Exception:
            code = f"레포지토리: {parsed['owner']}/{parsed['repo']}\n파일을 직접 선택해주세요."
        return {"code": code, "filename": "README.md", "source": url}

    if parsed["type"] == "file_direct":
        repo = g.get_repo(f"{parsed['owner']}/{parsed['repo']}")
        try:
            content = repo.get_contents(parsed["path"])
            if isinstance(content, list):
                raise ValueError("디렉토리입니다. 파일을 지정해주세요.")
            code = content.decoded_content.decode("utf-8")
        except Exception as e:
            raise ValueError(f"파일을 읽을 수 없습니다 ({parsed['path']}): {str(e)}")
        return {"code": code, "filename": parsed["path"].split('/')[-1], "source": url}

    raise ValueError(f"지원하지 않는 GitHub URL 형식: {url}")


async def fetch_webpage_code(url: str) -> dict:
    """웹페이지에서 코드 블록 추출"""
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; CodeReviewBot/1.0)"},
        timeout=15.0,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # <code>, <pre> 태그에서 코드 추출
    code_blocks = []
    for tag in soup.find_all(["pre", "code"]):
        text = tag.get_text().strip()
        if len(text) > 50:  # 의미있는 코드만
            code_blocks.append(text)

    if code_blocks:
        code = "\n\n# --- 코드 블록 구분선 ---\n\n".join(code_blocks[:10])
    else:
        # 코드 블록 없으면 페이지 텍스트에서 코드처럼 보이는 부분 추출
        code = soup.get_text()[:5000]

    return {
        "code": code,
        "filename": url.split("/")[-1] or "webpage",
        "source": url,
        "blocks_found": len(code_blocks),
    }


async def fetch_code(input_type: str, content: str) -> dict:
    """입력 타입에 따른 코드 취득"""
    try:
        if input_type == "github":
            return await fetch_github_code(content)
        elif input_type == "url":
            return await fetch_webpage_code(content)
        elif input_type == "code":
            return {"code": content, "filename": "direct_input", "source": "직접 입력"}
        else:
            raise ValueError(f"알 수 없는 입력 타입: {input_type}")
    except Exception as e:
        msg = str(e)
        # GitHub API 에러를 읽기 쉽게 변환
        if "401" in msg:
            raise RuntimeError("GitHub 인증 실패: .env의 GITHUB_TOKEN을 확인하거나 공개 레포를 사용해주세요.")
        if "404" in msg:
            raise RuntimeError("GitHub 레포/파일을 찾을 수 없습니다. 비공개 레포는 GITHUB_TOKEN이 필요합니다.")
        if "403" in msg:
            raise RuntimeError("GitHub API 호출 한도 초과(Rate Limit). GITHUB_TOKEN을 설정하면 한도가 늘어납니다.")
        raise
