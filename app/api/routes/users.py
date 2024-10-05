from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
users_table = dynamodb.Table("users")

# Initialize the router
router = APIRouter()

# Define the data models using Pydantic


class UserBase(BaseModel):
    wallet_public_key: str = Field(..., description="User's public wallet key")
    telegram_username: str = Field(..., description="User's unique username")
    is_registered: bool = Field(default=True, description="User registration status")


class UserCreate(UserBase):
    pass


class User(UserBase):
    created_at: str = Field(..., description="Timestamp of user creation")
    updated_at: str = Field(..., description="Timestamp of last user update")


class UserUpdate(BaseModel):
    wallet_public_key: Optional[str] = Field(
        None, description="User's public wallet key"
    )
    telegram_username: Optional[str] = Field(None, description="User's unique username")
    is_registered: Optional[bool] = Field(None, description="User registration status")


def get_users_table():
    return users_table


# Helper function to format user data


def format_user(user):
    return {
        "wallet_public_key": user["wallet_public_key"],
        "telegram_username": user["telegram_username"],
        "is_registered": user["is_registered"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


# Create a new user


@router.post("/users", response_model=User, status_code=201)
async def create_user(
    user: UserCreate, table: dynamodb.Table = Depends(get_users_table)
):
    new_user = user.dict()
    new_user["created_at"] = datetime.utcnow().isoformat()
    new_user["updated_at"] = new_user["created_at"]

    try:
        table.put_item(Item=new_user)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    return format_user(new_user)


# Get all users


@router.get("/users", response_model=List[User])
async def get_users(table: dynamodb.Table = Depends(get_users_table)):
    try:
        response = table.scan()
        users = response.get("Items", [])
        return [format_user(user) for user in users]
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve users: {str(e)}"
        )


# Get a specific user by ID


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, table: dynamodb.Table = Depends(get_users_table)):
    try:
        response = table.get_item(Key={"id": user_id})
        user = response.get("Item")
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return format_user(user)
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve user: {str(e)}"
        )


# Update a user


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    table: dynamodb.Table = Depends(get_users_table),
):
    update_data = user_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_expression = "SET " + ", ".join(f"#{k}=:{k}" for k in update_data.keys())
    update_expression += ", updated_at=:updated_at"

    expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
    expression_attribute_values = {f":{k}": v for k, v in update_data.items()}
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()

    try:
        response = table.update_item(
            Key={"id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        updated_user = response.get("Attributes")
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return format_user(updated_user)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


# Delete a user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str, table: dynamodb.Table = Depends(get_users_table)):
    try:
        response = table.delete_item(Key={"id": user_id}, ReturnValues="ALL_OLD")
        deleted_user = response.get("Attributes")
        if not deleted_user:
            raise HTTPException(status_code=404, detail="User not found")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
