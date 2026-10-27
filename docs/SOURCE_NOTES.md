# Source Notes

## 구현 근거
발표자료에서 다음 항목이 명확히 정의되어 있습니다.

- API Gateway REST API
- Lambda `fraud-handler`
- Python 3.12 / 128MB / Timeout 30초
- DynamoDB `fraud-reports`
- PK: `suspicion_id`
- GSI 1: `suspect_account + created_at`
- GSI 2: `status + created_at`
- CloudWatch 로그
- 4개 REST Endpoint
- Request / Response Schema
- fraud_type별 risk_level 규칙
- 동일 계좌 3건 이상 CRITICAL

## 코드 기준
공개 `src/` 코드는 팀 발표자료의 API·데이터 설계를 기준으로 작성했습니다. 당시 Lambda 원본 소스와 동일한 버전은 아닙니다.

## 리스크 판정 예시의 불일치
발표자료의 상세 규칙표는 다음과 같이 정의합니다.

- VOICE_PHISHING 100만원 이상 → HIGH
- VOICE_PHISHING 100만원 미만 → MEDIUM

하지만 다른 시나리오 슬라이드 중 하나에는 `VOICE_PHISHING + 500,000원 → HIGH`라는 예시가 존재합니다.

현재 코드는 **상세 규칙표**를 기준으로 500,000원을 `MEDIUM`으로 처리합니다.

## IAM 표현 차이
한 슬라이드에는 `DynamoDB FullAccess`라는 표현이 있고, 같은 발표자료에는 '최소 권한 원칙'도 명시되어 있습니다.  
현재 SAM 템플릿은 대상 테이블에 필요한 DynamoDB CRUD 권한만 부여합니다.
