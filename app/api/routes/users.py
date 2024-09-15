from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')  # Replace with your AWS region
users_table = dynamodb.Table('users')

# Initialize the router
router = APIRouter()

# Define the data model for User using Pydantic
class User(BaseModel):
    user_id: int
    wallet: str
    wallet_type: str

# General GET endpoint to retrieve all users
@router.get("/", response_model=List[Dict])
def list_users():
    try:
        response = users_table.scan()
        items = response.get('Items')
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST endpoint to add a new user
@router.post("/", response_model=User)
def create_user(user: User):
    try:
        # Prepare the item to insert into DynamoDB
        users_table.put_item(
            Item={
                "user_id": {"N": str(user.user_id)},
                "wallet": {"S": user.wallet},
                "wallet_type": {"S": user.wallet_type},
            }
        )
        return user
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

