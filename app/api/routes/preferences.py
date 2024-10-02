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


class Platform(BaseModel):
    platform_name: str
    username: str


class Action(BaseModel):
    # Need to generate id based on increment, action definitions will be determined
    action_type_id: int
    coin_name: Optional[str] = None
    # Changed to float for more precise coin prices
    coin_price: Optional[Decimal] = None


class Preferences(BaseModel):
    # Each preference set will be unique to the user_id
    user_id: int
    platforms: List[Platform]
    actions: List[Action]


# Initialize the router
router = APIRouter()

# Function to get user preferences


def get_user_preferences(user_id: int) -> Optional[dict]:
    try:
        response = preferences_table.get_item(Key={"user_id": user_id})
        item = response.get("Item")
        if not item:
            return None

        return {
            "user_id": item["user_id"],
            "platforms": item.get("platforms", []),
            "actions": item.get("actions", []),
        }
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simulate foreign key enforcement: Check if user exists


def check_user_exists(user_id: int):
    try:
        response = users_table.get_item(Key={"user_id": user_id})
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
def read_user_preferences(user_id: int):
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

        # Prepare data for DynamoDB
        platforms_data = [
            {"platform_name": platform.platform_name, "username": platform.username}
            for platform in preferences.platforms
        ]

        actions_data = []
        for action in preferences.actions:
            action_item = {
                "action_type_id": action.action_type_id,
            }
            if action.coin_name:
                action_item["coin_name"] = action.coin_name
            if action.coin_price is not None:
                action_item["coin_price"] = action.coin_price
            actions_data.append(action_item)

            # Insert into table

            preferences_table.put_item(
                Item={
                    "user_id": preferences.user_id,  # Ensure this is an integer
                    "platforms": platforms_data,
                    "actions": actions_data,
                }
            )
        return preferences

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
