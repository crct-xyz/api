from fastapi import APIRouter, HTTPException, Query
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
from app.api.models.actions import Action

dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
actions_table = dynamodb.Table("actions")
users_table = dynamodb.Table("users")

# Initialize the router
router = APIRouter()

# Function to check if the user exists (simulated foreign key enforcement)


def check_user_exists(wallet_public_key: str):
    try:
        response = users_table.get_item(
            Key={"wallet_public_key": wallet_public_key})
        if "Item" not in response:
            raise HTTPException(
                status_code=404,
                detail=f"User with wallet_public_key {wallet_public_key} does not exist",
            )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# General GET endpoint to retrieve all actions
@router.get("/", response_model=List[Action])
async def list_actions():
    try:
        response = actions_table.scan()
        return response.get("Items", [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# POST endpoint to add a new action with foreign key enforcement
@router.post("/", response_model=Action)
async def create_action(action: Action):
    # Simulate foreign key enforcement
    check_user_exists(
        action.user_id
    )  # user_id in action is actually the wallet_public_key
    try:
        actions_table.put_item(
            Item=action.dict(), ConditionExpression="attribute_not_exists(action_id)"
        )
        return action
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=400, detail="Action with this action_id already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


# GET specific action


@router.get("/", response_model=List[Action])
async def list_actions(
    filter_key: Optional[str] = Query(
        None, description="Attribute to filter on"),
    filter_value: Optional[str] = Query(
        None, description="Value to filter by"),
    limit: Optional[int] = Query(
        None, description="Number of items to return"),
    last_evaluated_key: Optional[str] = Query(
        None, description="Last evaluated key for pagination"
    ),
):
    try:
        scan_kwargs = {}
        if filter_key and filter_value:
            scan_kwargs["FilterExpression"] = Attr(filter_key).eq(filter_value)
        if limit:
            scan_kwargs["Limit"] = limit
        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = {
                "action_id": int(last_evaluated_key)}

        response = actions_table.scan(**scan_kwargs)

        items = response.get("Items", [])

        # Transform items to match the Action model
        transformed_items = []
        for item in items:
            transformed_item = {
                "action_id": item["action_id"],
                "action_type_id": item["action_type_id"],
                "user_id": item["user_id"],
                "transaction_index": item.get("transaction_index"),
                "transaction_type": item.get("transaction_type"),
                "payload": item["payload"],
            }
            transformed_items.append(Action(**transformed_item))

        return transformed_items

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# PUT endpoint to update an existing action
@router.put("/{action_id}", response_model=Action)
async def update_action(action_id: int, action: Action):
    if action_id != action.action_id:
        raise HTTPException(
            status_code=400, detail="Path action_id does not match body action_id"
        )
    check_user_exists(
        action.user_id
    )  # user_id in action is actually the wallet_public_key
    try:
        response = actions_table.update_item(
            Key={"action_id": action_id},
            UpdateExpression="set action_type_id=:ati, user_id=:uid, payload=:p",
            ExpressionAttributeValues={
                ":ati": action.action_type_id,
                ":uid": action.user_id,
                ":p": action.payload,
            },
            ReturnValues="ALL_NEW",
        )
        return Action(**response["Attributes"])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE endpoint to remove an action
@router.delete("/{action_id}", response_model=Dict[str, str])
async def delete_action(action_id: int):
    try:
        actions_table.delete_item(Key={"action_id": action_id})
        return {"message": f"Action with action_id {action_id} has been deleted"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
