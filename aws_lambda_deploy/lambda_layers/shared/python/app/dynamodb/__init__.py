"""
DynamoDB repository layer for MetaAds serverless.

Replaces SQLAlchemy + SQLite with boto3 + DynamoDB single-table design.

Table structure:
    PK / SK form the primary key.
    GSI1 and GSI2 cover all remaining access patterns.

Usage:
    from app.dynamodb.user_repo import UserRepo
    from app.dynamodb.niche_repo import NicheRepo
    from app.dynamodb.ad_repo import AdRepo
    from app.dynamodb.page_repo import PageRepo
    from app.dynamodb.collection_repo import CollectionRepo
"""
