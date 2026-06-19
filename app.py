"""코드 리뷰 AI 에이전트 - FastAPI 메인 서버"""
import os
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="코드 리뷰 AI 에이전트",
    description="GitHub URL, 웹페이지, 소스코드 실시간 AI 코드 분석 서비스",
    version="1.0.0",
)


# ─── Request/Response 모델 ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    input_type: str           # "github" | "url" | "code"
    content: str              # URL 또는 소스코드
    language: str = "auto"
    analysis_types: list[str] = ["code", "bug", "perf", "refactor", "test"]
    provider: Optional[str] = None  # "gemini" | "openai" (없으면 env 사용)
    api_key: Optional[str] = None   # 사용자 입력 API 키


# ─── 라우터 ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page():
    return FileResponse("templates/analyze.html")

@app.get("/view-app", response_class=HTMLResponse)
async def view_app():
    with open("app.py", "r", encoding="utf-8") as f:
        code_content = f.read()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>app.py 소스코드 보기</title>
        <style>
            body {{ font-family: 'SF Mono', 'Fira Code', monospace; background-color: #f8fafc; padding: 24px; color: #0f172a; line-height: 1.6; margin: 0; }}
            .header-bar {{ background-color: #ffffff; padding: 16px 24px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; gap: 12px; position: sticky; top: 0; z-index: 10; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
            .header-bar h1 {{ margin: 0; font-family: 'Outfit', sans-serif; font-size: 1.25rem; color: #4f46e5; }}
            .container {{ max-width: 1200px; margin: 24px auto; }}
            pre {{ background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; overflow-x: auto; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); font-size: 0.9rem; }}
            code {{ font-family: inherit; }}
        </style>
    </head>
    <body>
        <div class="header-bar">
            <span>📄</span>
            <h1>app.py 소스코드</h1>
        </div>
        <div class="container">
            <pre><code>{code_content.replace('<', '&lt;').replace('>', '&gt;')}</code></pre>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "provider": os.getenv("LLM_PROVIDER", "openai"),
        "version": "1.0.0",
    }


@app.post("/api/v1/fetch-code")
async def fetch_code_endpoint(request: AnalyzeRequest):
    """코드 미리 가져오기 (스트리밍 전 메타데이터 확인용)"""
    from utils.code_fetcher import fetch_code, detect_language
    try:
        result = await fetch_code(request.input_type, request.content)
        lang = request.language if request.language != "auto" else detect_language(
            result["code"], result.get("filename", "")
        )
        result["detected_language"] = lang
        result["code_preview"] = result["code"][:500] + ("..." if len(result["code"]) > 500 else "")
        result["code_length"] = len(result["code"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    """실시간 스트리밍 분석 - Server-Sent Events"""
    from utils.code_fetcher import fetch_code, detect_language
    import agents.code_analyzer as code_analyzer
    import agents.bug_detector as bug_detector
    import agents.perf_optimizer as perf_optimizer
    import agents.refactor_suggester as refactor_suggester
    import agents.test_generator as test_generator

    # 요청된 provider 임시 설정
    if request.provider:
        os.environ["LLM_PROVIDER"] = request.provider
    if request.api_key:
        provider_upper = request.provider.upper() if request.provider else "OPENAI"
        os.environ[f"{provider_upper}_API_KEY"] = request.api_key

    agent_map = {
        "code": ("📊 코드 분석", code_analyzer),
        "bug": ("🐛 버그 탐지", bug_detector),
        "perf": ("⚡ 성능 최적화", perf_optimizer),
        "refactor": ("💡 리팩토링 제안", refactor_suggester),
        "test": ("✅ 테스트 생성", test_generator),
    }

    async def event_generator():
        try:
            # 1. 코드 가져오기
            yield f"data: {json.dumps({'type': 'status', 'message': '🔍 코드를 가져오는 중...'})}\n\n"
            await asyncio.sleep(0)

            fetch_result = await fetch_code(request.input_type, request.content)
            code = fetch_result["code"]
            language = request.language if request.language != "auto" else detect_language(
                code, fetch_result.get("filename", "")
            )

            yield f"data: {json.dumps({'type': 'meta', 'data': {'filename': fetch_result.get('filename', ''), 'language': language, 'lines': len(code.splitlines()), 'source': fetch_result.get('source', '')}})}\n\n"
            await asyncio.sleep(0)

            # 2. 선택된 분석 모듈 순차 실행
            for analysis_type in request.analysis_types:
                if analysis_type not in agent_map:
                    continue

                label, agent = agent_map[analysis_type]
                yield f"data: {json.dumps({'type': 'section_start', 'label': label, 'analysis_type': analysis_type})}\n\n"
                await asyncio.sleep(0)

                try:
                    async for chunk in agent.analyze(code, language):
                        yield f"data: {json.dumps({'type': 'chunk', 'analysis_type': analysis_type, 'content': chunk})}\n\n"
                        await asyncio.sleep(0)
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'analysis_type': analysis_type, 'message': str(e)})}\n\n"

                yield f"data: {json.dumps({'type': 'section_end', 'analysis_type': analysis_type})}\n\n"
                await asyncio.sleep(0)

            yield f"data: {json.dumps({'type': 'done', 'message': '✅ 전체 분석 완료!'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'fatal_error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("APP_PORT", 8000))),
        reload=os.getenv("DEBUG", "true").lower() == "true",
    )
