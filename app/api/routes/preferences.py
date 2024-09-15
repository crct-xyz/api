from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')  # Replace 'your-region' with your AWS region
preferences_table = dynamodb.Table('preferences')
users_table = dynamodb.Table('users')

# Define the data models for the preferences API 
class Platform(BaseModel):
    platform_name: str
    username: str

class Action(BaseModel):
    # Need to generate id based on increment, action definitions will be determined
    action_type_id: int
    coin_name: Optional[str] = None
    coin_price: Optional[int] = None

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
        item = response.get('Item')
        if not item:
            return None

        return {
            "user_id": item['user_id'],
            "platforms": item.get('platforms'),
            "actions": item.get('actions')
        }
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simulate foreign key enforcement: Check if user exists
def check_user_exists(user_id: int):
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="User does not exist")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint to retrieve user preferences
@router.get("/", response_model=List[Preferences])
def list_user_preferences():
    try:
        response = preferences_table.scan()
        items = response.get('Items')

        # Directly return the list of items
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=Preferences)
def read_user_preferences(user_id: int):
    preferences = get_user_preferences(user_id)
    if preferences is None:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences

# POST endpoint to add preferences
@router.post("/", response_model=Preferences)
def create_user_preferences(preferences: Preferences):
    # Simulate foreign key enforcement THIS IS IMPORTANT for now since using dynamo we need to make sure this is enforced API side
    check_user_exists(preferences.user_id)

    # Prepare data for DynamoDB -- Needs more work to setup for a larger variety of actions
    platforms_data = [
        {"M": {"platform_name": {"S": platform.platform_name}, "username": {"S": platform.username}}}
        for platform in preferences.platforms
    ]

    actions_data = [
        {
            "M": {
                "action_type_id": {"N": str(action.action_type_id)},
                **({"coin_name": {"S": action.coin_name}} if action.coin_name else {}),
                **({"coin_price": {"N": str(action.coin_price)}} if action.coin_price is not None else {})
            }
        }
        for action in preferences.actions
    ]

    # Insert into table
    try:
        preferences_table.put_item(
            Item={
                "user_id": {"N": str(preferences.user_id)},
                "platforms": {"L": platforms_data},
                "actions": {"L": actions_data}
            }
        )
        return preferences
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
