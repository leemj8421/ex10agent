"""테스트 코드 생성 에이전트 - 단위/엣지/통합 테스트 자동 생성"""
from typing import AsyncGenerator
from llm.providers import get_llm

PROMPT_TEMPLATE = """당신은 테스트 전문 엔지니어입니다. 아래 코드에 대한 **완전한 테스트 코드**를 생성해주세요.

## 분석 언어: {language}

## 분석 대상 코드:
```
{code}
```

## 테스트 코드 생성 범주:

### ✅ 1. Unit Test (단위 테스트)
- 각 함수/메서드의 정상 케이스 테스트
- 명확한 테스트 이름 (test_함수명_상황_기대결과)
- Given-When-Then 패턴 적용
- assert 문 상세 작성

### 🔲 2. Edge Case Test (경계값 테스트)
- 빈 입력 (None, empty string, [], {{}})
- 최대값/최소값/경계값
- 음수/0/양수 구분
- 특수문자/유니코드 입력
- 매우 큰 데이터셋

### ⚠️ 3. Exception Test (예외 케이스 테스트)
- 잘못된 타입 입력
- 예외 발생 케이스 검증
- pytest.raises 활용
- 예외 메시지 내용 검증

### 🔗 4. Mock/Stub 테스트 (외부 의존성)
- 외부 API 호출 모킹
- 데이터베이스 연동 모킹
- unittest.mock / pytest-mock 활용
- 의존성 격리 테스트

### 📊 5. 테스트 커버리지 분석
- 생성된 테스트의 예상 커버리지
- 미커버 케이스 목록
- 추가 권장 테스트 항목

## 출력 요구사항:
- 언어에 맞는 테스트 프레임워크 사용 (Python: pytest, JS: Jest/Vitest, Java: JUnit)
- 바로 실행 가능한 완전한 테스트 코드
- 각 테스트에 한국어 독스트링/주석 포함
- 파일 최상단에 필요한 import 문 모두 포함
"""


async def analyze(code: str, language: str = "auto") -> AsyncGenerator[str, None]:
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(code=code, language=language)
    async for chunk in llm.stream(prompt):
        yield chunk
