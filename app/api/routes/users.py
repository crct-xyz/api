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

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
users_table = dynamodb.Table("users")

# Initialize the router
router = APIRouter()


# Define the data models using Pydantic
class UserInput(BaseModel):
    wallet_public_key: str


class UserResponse(BaseModel):
    wallet_public_key: str
    is_registered: bool


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


# POST endpoint to add a new user or update existing user
@router.post("/", response_model=UserResponse)
async def create_or_update_user(user_input: UserInput, request: Request):
    logger.info(
        f"Received POST request to create or update user: {user_input.wallet_public_key}"
    )
    try:
        # Log the incoming request body
        body = await request.json()
        logger.debug(f"Request body: {body}")

        # Check if the wallet already exists
        existing_user = users_table.get_item(
            Key={"wallet_public_key": user_input.wallet_public_key}
        ).get("Item")

        if existing_user:
            # Wallet already exists, update is_registered to True if it wasn't already
            is_registered = existing_user.get("is_registered", False)
            if not is_registered:
                item = {
                    "wallet_public_key": user_input.wallet_public_key,
                    "is_registered": True,
                }
                users_table.put_item(Item=item)
                logger.info(
                    f"User {user_input.wallet_public_key} updated: is_registered set to True"
                )
            else:
                logger.info(
                    f"User {user_input.wallet_public_key} already registered")
        else:
            # New wallet, add to database
            item = {
                "wallet_public_key": user_input.wallet_public_key,
                "is_registered": True,  # Set to True as we're registering it now
            }
            users_table.put_item(Item=item)
            logger.info(
                f"New user {user_input.wallet_public_key} added successfully")

        # Return the updated or created user
        return UserResponse(
            wallet_public_key=user_input.wallet_public_key, is_registered=True
        )

    except ClientError as e:
        logger.error(f"ClientError during put_item: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to add or update user in the database"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during put_item: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# GET endpoint to check if a wallet is registered
@router.get("/{wallet_public_key}", response_model=UserResponse)
async def check_wallet_registration(wallet_public_key: str):
    logger.info(
        f"Received GET request to check wallet registration: {wallet_public_key}"
    )
    try:
        response = users_table.get_item(
            Key={"wallet_public_key": wallet_public_key})
        user = response.get("Item")

        if user:
            return UserResponse(
                wallet_public_key=user["wallet_public_key"],
                is_registered=user.get("is_registered", False),
            )
        else:
            return UserResponse(
                wallet_public_key=wallet_public_key, is_registered=False
            )

    except ClientError as e:
        logger.error(f"ClientError during get_item: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to check wallet registration"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during get_item: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

