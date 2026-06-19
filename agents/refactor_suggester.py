"""리팩토링 제안 에이전트 - 디자인 패턴, 구조 개선, Dead Code 제거"""
from typing import AsyncGenerator
from llm.providers import get_llm

PROMPT_TEMPLATE = """당신은 소프트웨어 아키텍트입니다. 아래 코드에 대한 **리팩토링 제안**을 해주세요.

## 분석 언어: {language}

## 분석 대상 코드:
```
{code}
```

## 리팩토링 분석 항목:

### 💡 1. 디자인 패턴 적용 제안
- 현재 코드에 적합한 디자인 패턴 식별
- 팩토리(Factory), 전략(Strategy), 데코레이터(Decorator), 옵저버(Observer) 등
- 패턴 적용 전/후 코드 비교
- 적용 이유 및 장점 설명

### 🔧 2. Extract Method/Class 제안
- 긴 함수를 역할별로 분리 (단일 책임 원칙)
- 20줄 이상 함수 분리 권고
- 클래스 분리 기회 식별
- 리팩토링 후 예시 코드

### 🗑️ 3. Dead Code 제거
- 사용되지 않는 변수/함수/임포트 탐지
- 도달 불가능한 코드(Unreachable Code)
- 중복 정의 식별
- 제거 후 클린 코드 예시

### 🏗️ 4. 코드 구조 개선
- 복잡한 조건문을 Early Return/Guard Clause로 단순화
- 중첩 루프/조건문 평탄화
- 매직 넘버/문자열을 상수로 추출
- 함수 파라미터 수 최적화 (5개 이상 시 객체 패턴 권장)

### 📦 5. 모듈화 및 재사용성
- 공통 로직 유틸리티 함수화
- 의존성 주입(DI) 패턴 적용 기회
- 인터페이스/추상 클래스 도입 제안
- 테스트 용이성 개선 방향

### ✅ 6. 최종 리팩토링 버전 코드
전체 개선사항을 반영한 완성된 리팩토링 코드를 제공해주세요.

마크다운 형식, 개선 전/후 비교, 이모지 활용하여 명확하게 작성해주세요.
"""


async def analyze(code: str, language: str = "auto") -> AsyncGenerator[str, None]:
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(code=code, language=language)
    async for chunk in llm.stream(prompt):
        yield chunk
