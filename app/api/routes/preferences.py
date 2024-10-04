from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize DynamoDB client
# Replace 'eu-central-1' with your AWS region if different
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
preferences_table = dynamodb.Table("preferences")
users_table = dynamodb.Table("users")

# Define the data models for the preferences API


class Preferences(BaseModel):
    # Each preference set will be unique to the user_id
    user_id: str
    telegram_user: str
    email: str


# Initialize the router
router = APIRouter()

# Function to get user preferences


def get_user_preferences(user_id: str) -> Optional[dict]:
    try:
        response = preferences_table.get_item(Key={"user_id": user_id})
        item = response.get("Item")
        if not item:
            return None

        return {
            "user_id": item["user_id"],
            "telegram_user": item["telegram_user"],
            "emails": item["emails"],
        }

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simulate foreign key enforcement: Check if user exists
def check_user_exists(user_id: str):
    try:
        response = users_table.get_item(Key={"wallet_public_key": user_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="User does not exist")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# GET endpoint to retrieve all user preferences


@router.get("/", response_model=List[Preferences])
def list_user_preferences():
    try:
        response = preferences_table.scan()
        items = response.get("Items", [])

        # Directly return the list of items
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# GET endpoint to retrieve preferences for a specific user


@router.get("/{user_id}", response_model=Preferences)
def read_user_preferences(user_id: str):
    preferences = get_user_preferences(user_id)
    if preferences is None:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


# POST endpoint to add preferences


@router.post("/", response_model=Preferences)
def create_user_preferences(preferences: Preferences):
    """
    Create user preferences in the DynamoDB 'preferences' table.
    """
    try:
        # Simulate foreign key enforcement: Ensure the user exists

        check_user_exists(preferences.user_id)

        preferences_table.put_item(
            Item={
                "user_id": preferences.user_id,
                "telegram_user": preferences.telegram_user,
                "email": preferences.email,
            }
        )
        return preferences

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
