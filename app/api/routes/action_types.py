from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional

# Initialize DynamoDB client
# Replace with your AWS region
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
actions_table = dynamodb.Table("action_types")

# Initialize the router
router = APIRouter()

# Define the data model for ActionTypes using Pydantic


class ActionType(BaseModel):
    type_id: int
    description: str
    json: str
    type_name: str


# General GET endpoint to retrieve all action types


@router.get("/", response_model=List[Dict])
def list_action_types():
    try:
        response = actions_table.scan()
        items = response.get("Items")
        return items
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# POST endpoint to add a new action type


@router.post("/", response_model=ActionType)
def create_action_type(action_type: ActionType):
    try:
        # Prepare the item to insert into DynamoDB
        actions_table.put_item(
            Item={
                "type_id": {"N": str(action_type.type_id)},
                "description": {"S": action_type.description},
                "json": {"S": action_type.json},
                "type_name": {"S": action_type.type_name},
            }
        )
        return action_type
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE endpoint to remove an action type
@router.delete("/{type_id}", response_model=Dict[str, str])
def delete_action_type(type_id: int):
    try:
        # Check if the action type exists
        response = actions_table.get_item(Key={"type_id": type_id})
        if "Item" not in response:
            raise HTTPException(
                status_code=404, detail=f"Action type with ID {type_id} not found"
            )

        # Delete the action type
        actions_table.delete_item(Key={"type_id": type_id})

        return {"message": f"Action type with ID {type_id} deleted successfully"}
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete action type: {str(e)}"
        )
