"""코드 분석 에이전트 - 복잡도, 컨벤션, 중복코드, 가독성 종합 분석"""
from typing import AsyncGenerator
from llm.providers import get_llm

PROMPT_TEMPLATE = """당신은 시니어 소프트웨어 엔지니어입니다. 아래 코드를 **코드 분석** 관점에서 상세히 분석해주세요.

## 분석 언어: {language}

## 분석 대상 코드:
```
{code}
```

## 분석 항목 (반드시 모두 포함):

### 📊 1. 코드 복잡도 분석
- Cyclomatic Complexity 추정 및 평가 (1-10 점수)
- 함수/클래스별 복잡도 현황
- 임계값(복잡도 10 이상) 초과 항목 경고

### 📋 2. 코딩 컨벤션 준수율
- PEP8(Python) / ESLint(JS) / Google Style Guide 기준 적용
- 위반 항목 목록 (라인 번호 포함)
- 준수율 퍼센트 산출

### 🔁 3. 중복 코드 탐지
- DRY 원칙 위반 패턴 식별
- 반복되는 로직 블록 표시
- 리팩토링 권고 방향

### 👁️ 4. 가독성 점수
- 변수명/함수명 명확성 (1-10)
- 주석 충분도 (1-10)
- 코드 구조 명확성 (1-10)
- 종합 가독성 점수 및 개선 제안

### ✅ 5. 종합 평가 및 즉시 적용 가능한 개선 코드

마크다운 형식으로 작성하고, 이모지를 적절히 사용하여 가독성을 높여주세요.
각 항목에서 심각도를 🔴 Critical / 🟡 Warning / 🟢 Info 로 태깅해주세요.
"""


async def analyze(code: str, language: str = "auto") -> AsyncGenerator[str, None]:
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(code=code, language=language)
    async for chunk in llm.stream(prompt):
        yield chunk
