from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional
import time

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
orders_table = dynamodb.Table("orders")

# Initialize the router
router = APIRouter()


class ActionEvent(BaseModel):
    event_type: str
    details: Dict


class Order(BaseModel):
    order_id: str
    app: str
    action_event: ActionEvent
    user_id: str
    timestamp: Optional[int] = None


@router.post("/", response_model=Order)
def create_order(order: Order):
    if order.timestamp is None:
        order.timestamp = int(time.time())

    try:
        orders_table.put_item(Item=order.dict())
        return order
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: str):
    try:
        response = orders_table.get_item(Key={"order_id": order_id})
        item = response.get("Item")
        if not item:
            raise HTTPException(
                status_code=404, detail=f"Order with ID {order_id} not found"
            )
        return Order(**item)
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve order: {str(e)}"
        )


@router.get("/", response_model=List[Order])
def list_orders():
    try:
        response = orders_table.scan()
        items = response.get("Items", [])
        return [Order(**item) for item in items]
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list orders: {str(e)}")


@router.delete("/{order_id}", response_model=Dict[str, str])
def delete_order(order_id: str):
    try:
        orders_table.delete_item(Key={"order_id": order_id})
        return {"message": f"Order with ID {order_id} deleted successfully"}
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete order: {str(e)}")


@router.put("/{order_id}", response_model=Order)
def update_order(order_id: str, order: Order):
    if order.order_id != order_id:
        raise HTTPException(
            status_code=400, detail="Order ID in path must match Order ID in body"
        )

    try:
        response = orders_table.put_item(Item=order.dict())
        return order
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update order: {str(e)}")
