"""
DynamoDB boto3 client singleton.

Provides a single shared Table resource reused across all warm Lambda
invocations.  Table name is injected via the DYNAMODB_TABLE env var set
by Terraform (value: "metaads-dev-table" or "metaads-prod-table").
"""

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr  # re-exported for convenience

_dynamodb = None
_table = None


def get_table():
    """
    Return the cached DynamoDB Table resource.

    On first call (cold start) the boto3 resource and Table object are
    created and stored in module-level globals so subsequent warm
    invocations reuse the connection pool.
    """
    global _dynamodb, _table

    if _table is None:
        table_name = os.environ.get("DYNAMODB_TABLE", "metaads-dev-table")
        _dynamodb = boto3.resource("dynamodb")
        _table = _dynamodb.Table(table_name)

    return _table


# GSI names — defined once here so repos don't hard-code strings
GSI1 = "GSI1"
GSI2 = "GSI2"

__all__ = ["get_table", "Key", "Attr", "GSI1", "GSI2"]
