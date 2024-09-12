from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

# Initialize the FastAPI app
app = FastAPI()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('UserPreferences')


# Define the data model for User Preferences using Pydantic
class UserPreferences(BaseModel):
    public_key: str
    last_updated: str
    telegram: bool
    telegram_username: str = None
    twitter: bool
    twitter_username: str = None


# Define a function to get user preferences from DynamoDB
def get_user_preferences(public_key: str) -> UserPreferences:
    try:
        response = table.get_item(Key={"PublicKey": public_key})
        item = response.get('Item')
        if not item:
            return None
        return UserPreferences(
            public_key=item['PublicKey'],
            last_updated=item['LastUpdated'],
            telegram=bool(item['Telegram']),
            telegram_username=item.get('TelegramUsername'),
            twitter=bool(item['Twitter']),
            twitter_username=item.get('TwitterUsername')
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


# Define the GET endpoint to retrieve user preferences
@app.get("/preferences/{public_key}", response_model=UserPreferences)
def read_user_preferences(public_key: str):
    preferences = get_user_preferences(public_key)
    if preferences is None:
        raise HTTPException(status_code=404, detail="User not found")
    return preferences

