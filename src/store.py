import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

class LocalStore:
    def __init__(self):
        self.items = {}

    def put_report(self, item: dict):
        self.items[item["suspicion_id"]] = dict(item)

    def get_report(self, suspicion_id: str):
        return self.items.get(suspicion_id)

    def update_status(self, suspicion_id: str, status: str):
        item = self.items.get(suspicion_id)
        if not item:
            return None
        item["status"] = status
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        return dict(item)

    def count_by_account(self, suspect_account: str):
        if not suspect_account:
            return 0
        return sum(1 for x in self.items.values() if x.get("suspect_account") == suspect_account)

    def list_by_statuses(self, statuses):
        items = [x for x in self.items.values() if x.get("status") in statuses]
        return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)

class DynamoDBStore:
    def __init__(self):
        table_name = os.getenv("TABLE_NAME", "fraud-reports")
        endpoint = os.getenv("DYNAMODB_ENDPOINT")
        kwargs = {}
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        self.table = boto3.resource("dynamodb", **kwargs).Table(table_name)

    def put_report(self, item: dict):
        safe = {
            k: (Decimal(v) if isinstance(v, float) else v)
            for k, v in item.items()
        }
        self.table.put_item(Item=safe)

    def get_report(self, suspicion_id: str):
        return self.table.get_item(Key={"suspicion_id": suspicion_id}).get("Item")

    def update_status(self, suspicion_id: str, status: str):
        now = datetime.now(timezone.utc).isoformat()
        response = self.table.update_item(
            Key={"suspicion_id": suspicion_id},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status, ":u": now},
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes")

    def count_by_account(self, suspect_account: str):
        if not suspect_account:
            return 0
        response = self.table.query(
            IndexName="suspect-account-created-at-index",
            KeyConditionExpression=Key("suspect_account").eq(suspect_account),
            Select="COUNT",
        )
        return int(response.get("Count", 0))

    def list_by_statuses(self, statuses):
        # 발표자료의 'scan 금지' 원칙을 지키기 위해 status GSI를 상태별 query합니다.
        items = []
        for status in statuses:
            response = self.table.query(
                IndexName="status-created-at-index",
                KeyConditionExpression=Key("status").eq(status),
                ScanIndexForward=False,
            )
            items.extend(response.get("Items", []))
        return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)

def build_store():
    if os.getenv("LOCAL_MODE", "false").lower() == "true":
        return LocalStore()
    return DynamoDBStore()
