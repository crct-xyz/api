import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO or WARNING in production
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Optional: Enable boto3 logging for debugging
# boto3.set_stream_logger('boto3.resources', logging.DEBUG)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
users_table = dynamodb.Table("users")

# Initialize the router
router = APIRouter()

# Define the data model for User using Pydantic


class User(BaseModel):
    user_id: str
    wallet_name: str
    wallet_public_key: str


# GET endpoint to retrieve all users


@router.get("/", response_model=List[Dict])
def list_users():
    logger.info("Received GET request to list users")
    try:
        response = users_table.scan()
        items = response.get("Items")
        logger.debug(f"Scan response: {items}")
        return items
    except ClientError as e:
        logger.error(f"ClientError during scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during scan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# POST endpoint to add a new user


# POST endpoint to add a new user
@router.post("/", response_model=User)
async def create_user(user: User, request: Request):
    logger.info(f"Received POST request to create user: {user}")
    try:
        # Log the incoming request body
        body = await request.json()
        logger.debug(f"Request body: {body}")

        # Log the type and value of user_id
        logger.debug(f"user.user_id type: {type(user.user_id)}")
        logger.debug(f"user.user_id value: {user.user_id}")

        # Prepare the item to insert into DynamoDB
        item = {
            "user_id": user.user_id,
            "wallet_name": user.wallet_name,
            "wallet_public_key": user.wallet_public_key,
        }
        logger.debug(f"Item to be inserted into DynamoDB: {item}")

        # Perform the PutItem operation
        users_table.put_item(Item=item)
        logger.info(f"User {user.user_id} added successfully")
        return user
    except ClientError as e:
        logger.error(f"ClientError during put_item: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to add user to the database"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during put_item: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
