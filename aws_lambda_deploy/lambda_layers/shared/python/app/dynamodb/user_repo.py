"""
User repository — replaces app/services/user_service.py + app/models/user.py.

Access patterns covered:
    get(clerk_id)           PK=USER#<id>  SK=METADATA
    get_by_email(email)     GSI1: GSI1PK=USER_EMAIL#<email>  GSI1SK=METADATA
    create(user)            PutItem (conditional: must not exist)
    update(user)            UpdateItem
    deactivate(clerk_id)    UpdateItem (is_active=False)
"""

from __future__ import annotations

from typing import Optional

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.dynamodb.client import get_table, GSI1
from app.dynamodb.models import User
from app.utils.ids import now_iso8601


class UserRepo:

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get(clerk_id: str) -> Optional[User]:
        """Return a User by Clerk ID, or None if not found."""
        table = get_table()
        resp = table.get_item(
            Key={"PK": User.pk(clerk_id), "SK": User.sk()}
        )
        item = resp.get("Item")
        return User.from_item(item) if item else None

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Return a User by email address (GSI1 lookup)."""
        table = get_table()
        resp = table.query(
            IndexName=GSI1,
            KeyConditionExpression=(
                Key("GSI1PK").eq(f"USER_EMAIL#{email}") &
                Key("GSI1SK").eq("METADATA")
            ),
            Limit=1,
        )
        items = resp.get("Items", [])
        return User.from_item(items[0]) if items else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(user: User) -> User:
        """
        Insert a new User.  Raises ValueError if the Clerk ID already exists.
        """
        table = get_table()
        now = now_iso8601()
        user.created_at = user.created_at or now
        user.updated_at = now

        try:
            table.put_item(
                Item=user.to_item(),
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError(f"User {user.id} already exists") from exc
            raise

        return user

    @staticmethod
    def create_or_update(user: User) -> User:
        """
        Upsert a User — used by the Clerk webhook (user.created / user.updated).
        """
        table = get_table()
        now = now_iso8601()

        existing = UserRepo.get(user.id)
        if existing:
            user.created_at = existing.created_at  # preserve original
        else:
            user.created_at = now

        user.updated_at = now
        table.put_item(Item=user.to_item())
        return user

    @staticmethod
    def update(clerk_id: str, **kwargs) -> Optional[User]:
        """
        Update specific fields on a User.  Accepted kwargs:
            first_name, last_name, image_url, email, is_active
        """
        table = get_table()

        allowed = {"first_name", "last_name", "image_url", "email", "is_active"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return UserRepo.get(clerk_id)

        updates["updated_at"] = now_iso8601()

        expr_parts = [f"#{k} = :{k}" for k in updates]
        update_expr = "SET " + ", ".join(expr_parts)
        expr_names = {f"#{k}": k for k in updates}
        expr_values = {f":{k}": v for k, v in updates.items()}

        table.update_item(
            Key={"PK": User.pk(clerk_id), "SK": User.sk()},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

        return UserRepo.get(clerk_id)

    @staticmethod
    def deactivate(clerk_id: str) -> None:
        """Soft-delete: set is_active=False (called on Clerk user.deleted webhook)."""
        UserRepo.update(clerk_id, is_active=False)
