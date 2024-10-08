from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

# Define the data model for Actions using Pydantic


class Action(BaseModel):
    action_id: int
    action_type_id: int
    user_id: str
    vault_id: Optional[str] = None
    transaction_index: Optional[int] = None
    transaction_type: Optional[str] = None
    payload: Dict
