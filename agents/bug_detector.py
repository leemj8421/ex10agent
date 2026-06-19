"""버그 탐지 에이전트 - 정적분석 + LLM 기반 잠재 버그 및 취약점 탐지"""
from typing import AsyncGenerator
from llm.providers import get_llm

PROMPT_TEMPLATE = """당신은 보안 전문 코드 리뷰어입니다. 아래 코드에서 **버그 및 취약점**을 탐지해주세요.

## 분석 언어: {language}

## 분석 대상 코드:
```
{code}
```

## 탐지 항목 (심각도별 분류):

### 🔴 Critical (즉시 수정 필요)
- Null/None 포인터 역참조
- 배열/인덱스 범위 초과
- SQL 인젝션 / XSS 취약점
- 인증/인가 결함
- 무한 루프 / 데드락 가능성

### 🟡 Warning (빠른 수정 권장)
- 미처리 예외 (bare except, uncaught exception)
- 리소스 누수 (파일, 커넥션 미닫기)
- 타입 불일치 / 암묵적 형변환
- 경쟁 조건(Race Condition) 가능성
- 하드코딩된 민감정보 (API Key, Password)

### 🟢 Info (개선 권장)
- 잠재적 로직 오류
- 엣지 케이스 미처리
- 예외 메시지 부실
- 로깅 부재

## 출력 형식:
각 발견 항목에 대해:
- **위치**: 함수명 또는 라인 번호 범위
- **문제 설명**: 왜 버그/취약점인지
- **예상 영향**: 어떤 상황에서 오류 발생
- **수정 코드**: 구체적인 수정 방법 및 코드

마지막에 **버그 탐지 종합 리포트** (발견 건수, 위험도 분포)를 작성해주세요.
"""


async def analyze(code: str, language: str = "auto") -> AsyncGenerator[str, None]:
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(code=code, language=language)
    async for chunk in llm.stream(prompt):
        yield chunk
