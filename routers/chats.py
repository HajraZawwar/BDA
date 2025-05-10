from fastapi import APIRouter, Form, Query, HTTPException
from bson import ObjectId
from datetime import datetime
from database import mongo_db
from jose import jwt, JWTError

router = APIRouter()

def get_user_id_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Send a message
@router.post("/send")
def send_message(
    token: str = Form(...),
    recipient_id: str = Form(...),
    message: str = Form(...)
):
    sender_id = get_user_id_from_token(token)

    chat = {
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "message": message,
        "timestamp": datetime.utcnow()
    }

    mongo_db["chats"].insert_one(chat)
    return {"message": "Message sent"}

# Get chat with another user
@router.get("/history/{user_id}")
def get_chat_history(user_id: str, token: str = Query(...)):
    current_user = get_user_id_from_token(token)

    chat_cursor = mongo_db["chats"].find({
        "$or": [
            {"sender_id": current_user, "recipient_id": user_id},
            {"sender_id": user_id, "recipient_id": current_user}
        ]
    }).sort("timestamp", 1)

    history = []
    for chat in chat_cursor:
        history.append({
            "from": chat["sender_id"],
            "to": chat["recipient_id"],
            "message": chat["message"],
            "timestamp": chat["timestamp"].isoformat()
        })

    return history

