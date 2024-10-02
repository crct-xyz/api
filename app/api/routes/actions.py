from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')  # Replace with your AWS region
actions_table = dynamodb.Table('actions')
users_table = dynamodb.Table('users')  # Reference to enforce the foreign key constraint

# Initialize the router
router = APIRouter()

# Define the data model for Actions using Pydantic
class Action(BaseModel):
    action_id: int
    action_json: str
    action_type_id: int
    user_id: int

# Function to check if the user exists (simulated foreign key enforcement)
def check_user_exists(user_id: int):
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail=f"User with user_id {user_id} does not exist")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

# General GET endpoint to retrieve all actions
@router.get("/", response_model=List[Dict])
def list_actions():
    try:
        response = actions_table.scan()
        items = response.get('Items')
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST endpoint to add a new action with foreign key enforcement
@router.post("/", response_model=Action)
def create_action(action: Action):
    # Simulate foreign key enforcement
    check_user_exists(action.user_id)

    try:
        # Prepare the item to insert into DynamoDB
        actions_table.put_item(
            Item={
                "action_id": {"N": str(action.action_id)},
                "action_json": {"S": action.action_json},
                "action_type_id": {"N": str(action.action_type_id)},
                "user_id": {"N": str(action.user_id)},
            }
        )
        return action
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

