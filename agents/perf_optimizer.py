"""성능 개선 에이전트 - 알고리즘 복잡도, N+1, 메모리 최적화 분석"""
from typing import AsyncGenerator
from llm.providers import get_llm

PROMPT_TEMPLATE = """당신은 성능 최적화 전문 엔지니어입니다. 아래 코드의 **성능 병목**을 분석하고 개선 방안을 제시해주세요.

## 분석 언어: {language}

## 분석 대상 코드:
```
{code}
```

## 성능 분석 항목:

### ⚡ 1. 시간 복잡도 분석
- 각 함수/알고리즘의 Big-O 표기법 분석
- O(n²) 이상 비효율 패턴 식별
- 최적화된 알고리즘 대안 제시
- 예상 성능 향상 수치 (예: 100만건 기준 기존 4.2초 → 개선 0.08초)

### 🗄️ 2. 데이터베이스 쿼리 최적화
- N+1 쿼리 문제 탐지
- 인덱스 미활용 패턴
- 불필요한 전체 조회 (SELECT *)
- 쿼리 최적화 및 배치 처리 방안

### 🧠 3. 메모리 효율성
- 불필요한 대용량 데이터 메모리 적재
- 제너레이터/이터레이터 활용 기회
- 캐싱 적용 가능 로직 식별
- 메모리 누수 패턴

### 🔄 4. 불필요한 반복 연산
- 루프 내 중복 연산
- 캐시 가능한 계산 결과
- 지연 평가(Lazy Evaluation) 적용 기회
- 병렬 처리 가능 구간

### ✅ 5. 최적화 우선순위 로드맵
- 높음/중간/낮음 우선순위로 분류
- 각 개선 시 예상 성능 향상율
- 즉시 적용 가능한 최적화 코드 예시

마크다운 형식으로 작성하고, 개선 전/후 코드를 나란히 보여주세요.
"""


async def analyze(code: str, language: str = "auto") -> AsyncGenerator[str, None]:
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(code=code, language=language)
    async for chunk in llm.stream(prompt):
        yield chunk
