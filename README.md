# Fraud Report Serverless API
### AWS Serverless Architecture 기반 금융사기 통합 신고 플랫폼

KT AIVLE School 팀 프로젝트에서 설계한 **금융사기 통합 신고 플랫폼**의 발표자료를 바탕으로 포트폴리오용으로 재구현한 서버리스 백엔드입니다.

발표자료에는 API Gateway, Lambda, DynamoDB, CloudWatch 중심의 아키텍처와 API·DynamoDB 설계가 상세히 정의되어 있었으나 전체 Lambda 원본 소스는 제공 자료에서 확인되지 않아, 이 저장소의 코드는 **해당 설계를 기준으로 다시 구현한 버전**입니다.

> 목표: 전화 대기·수기 접수 중심 흐름을  
> **모바일 신고 → 즉시 접수번호 발급 → 리스크 자동 판정 → 상태 관리**로 전환

## Architecture

```text
Client (Mobile / Web)
        ↓ HTTPS
API Gateway (REST API)
        ↓ Lambda Proxy
Lambda - fraud-handler
        ↓ put/get/query
DynamoDB - fraud-reports
        ↓
CloudWatch Logs
```

Lambda는 Stateless하게 유지하고 모든 신고 상태는 DynamoDB에 저장하는 구조입니다.

## API

| ID | Method | Endpoint | 설명 |
|---|---|---|---|
| FR-001 | POST | `/fraud-reports` | 신고 접수 |
| FR-002 | GET | `/fraud-reports` | 신고 목록 조회 |
| FR-003 | GET | `/fraud-reports/{id}` | 개별 신고 조회 |
| FR-004 | PUT | `/fraud-reports/{id}/status` | 신고 상태 변경 |

## Request Schema

`POST /fraud-reports`

```json
{
  "fraud_type": "VOICE_PHISHING",
  "victim_name": "홍길동",
  "victim_phone": "010-1234-5678",
  "amount": 500000,
  "suspect_account": "110-123-456789",
  "description": "상세 신고 내용"
}
```

허용 `fraud_type`

- `VOICE_PHISHING`
- `USED_TRADE`
- `INVESTMENT`
- `IDENTITY_THEFT`

허용 상태

- `RECEIVED`
- `REVIEWING`
- `CONFIRMED`
- `DISMISSED`
- `CLOSED`

## Risk Rule

발표자료의 상세 규칙표를 기준으로 구현했습니다.

| fraud_type | 조건 | risk_level |
|---|---|---|
| VOICE_PHISHING | 100만원 이상 | HIGH |
| VOICE_PHISHING | 100만원 미만 | MEDIUM |
| USED_TRADE | 100만원 이상 | HIGH |
| USED_TRADE | 100만원 미만 | MEDIUM |
| INVESTMENT | 금액 무관 | HIGH |
| IDENTITY_THEFT | 금액 무관 | HIGH |
| 동일 의심계좌 3건 이상 | 유형 무관 | CRITICAL |

동일 계좌 연쇄 신고는 `suspect_account + created_at` GSI로 조회합니다.

## DynamoDB Design

Table: `fraud-reports`

- PK: `suspicion_id`
- Billing: On-Demand
- GSI 1: `suspect_account + created_at`
  - 동일 계좌 연쇄 신고 탐지
- GSI 2: `status + created_at`
  - 상태별 미처리 신고 조회

발표자료의 원칙에 맞춰 `scan()` 대신 GSI `query()`를 사용합니다.

## Project Structure

```text
fraud-report-serverless/
├── src/
│   ├── lambda_function.py
│   ├── risk.py
│   ├── validation.py
│   └── store.py
├── tests/
│   ├── test_handler.py
│   └── test_risk.py
├── docs/
│   └── SOURCE_NOTES.md
├── template.yaml
├── requirements.txt
├── .env.example
└── README.md
```

## Local Test

API Gateway 없이 로컬 메모리 저장소로 Lambda 핸들러를 테스트할 수 있습니다.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install & test:

```bash
pip install -r requirements.txt
pytest -q
```

## Access control and deployment warning

The SAM template requires AWS IAM authorization (SigV4 signed requests with appropriately scoped `execute-api:Invoke` permission) for `GET /fraud-reports`, `GET /fraud-reports/{id}`, and `PUT /fraud-reports/{id}/status`. **A valid IAM identity alone is not sufficient**; the caller must be granted an appropriate execute-api resource ARN. Those endpoints must not be exposed through unauthenticated proxies.

`POST /fraud-reports` remains open as a demonstration of public intake. **Do not deploy publicly with real personal data** until rate limits, abuse protection, privacy retention/deletion, access logs and least-privilege access controls have been designed and tested. The default example includes personal-data fields but does not establish production compliance. In local tests the Lambda handler itself remains unauthenticated because enforcement occurs at API Gateway.

## AWS SAM Deploy

AWS SAM CLI가 설치되어 있다면:

```bash
sam build
sam deploy --guided
```

`template.yaml`은 다음 리소스를 생성합니다.

- API Gateway
- Lambda (Python 3.12 / 128MB / 30s)
- DynamoDB On-Demand
- GSI 2개
- Lambda 실행 권한

CloudWatch Logs는 Lambda 실행 시 자동 생성됩니다.

## Serverless Design Principles

### Event-Driven
API Gateway 요청이 들어올 때만 Lambda가 실행됩니다.

### Stateless
Lambda 함수 내부에는 신고 상태를 저장하지 않고 DynamoDB에 저장합니다.

### Auto-Scale
Lambda와 DynamoDB On-Demand의 관리형 확장 기능을 활용하는 구조입니다.

## Source Fidelity

이 저장소는 **발표자료의 서버리스 아키텍처와 인터페이스 설계를 실제 코드로 재구현한 프로젝트**입니다.  
발표자료 내부에서 서로 다르게 적힌 리스크 예시는 임의로 숨기지 않고 `docs/SOURCE_NOTES.md`에 기록했습니다.
