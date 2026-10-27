# Fraud Report Serverless API
### AWS Serverless Architecture 기반 금융사기 통합 신고 플랫폼

KT AIVLE School 팀 프로젝트에서 설계한 **금융사기 통합 신고 플랫폼**의 API를 AWS Serverless 구조로 구현했습니다. 공개 코드는 당시 발표자료의 API·데이터 설계를 기준으로 작성했습니다.

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

## 접근 제어 및 배포 주의사항

SAM 템플릿의 신고 조회·상태 변경 API는 AWS IAM 인증을 사용합니다. SigV4 서명과 해당 경로에 대한 `execute-api:Invoke` 권한이 필요하며, 인증 없는 프록시로 공개하면 안 됩니다.

`POST /fraud-reports`는 데모용 공개 접수 경로입니다. 실제 개인정보를 처리하려면 요청 제한, 악용 방지, 보관·삭제 정책, 접근 기록 및 최소 권한 설계가 먼저 필요합니다. 로컬에서 Lambda 함수를 직접 호출할 때는 API Gateway의 IAM 인증이 적용되지 않습니다.

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

## 설계 자료

발표자료의 구조와 위험도 규칙을 구현 기준으로 삼았습니다. 자료에 기록된 리스크 규칙의 표기 차이는 [`docs/SOURCE_NOTES.md`](docs/SOURCE_NOTES.md)에 정리했습니다.
