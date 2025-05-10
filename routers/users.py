from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from database import mongo_db
from jose import jwt, JWTError
from datetime import datetime
from fastapi import Path

router = APIRouter()

# Token decode utility
def get_user_id_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Route to get user's profile + posts
@router.get("/me")
def get_my_profile(token: str = Query(...)):
    user_id = get_user_id_from_token(token)

    user = mongo_db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts_cursor = mongo_db["posts"].find({"user_id": user_id}).sort("created_at", -1)
    posts = []
    for post in posts_cursor:
        posts.append({
            "caption": post["caption"],
            "image_url": post["image_url"],
            "likes": len(post.get("likes", [])),
            "comments": len(post.get("comments", [])),
            "created_at": post["created_at"].isoformat()
        })

    return {
        "username": user["username"],
        "avatar_url": user.get("avatar_url"),
        "posts": posts
    }

# Follow a user
@router.post("/follow/{target_id}")
def follow_user(token: str = Query(...), target_id: str = Path(...)):
    user_id = get_user_id_from_token(token)

    if user_id == target_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    mongo_db["followers"].update_one(
        {"user_id": user_id},
        {"$addToSet": {"follows": target_id}},
        upsert=True
    )
    return {"message": f"Now following {target_id}"}

# Unfollow a user
@router.post("/unfollow/{target_id}")
def unfollow_user(token: str = Query(...), target_id: str = Path(...)):
    user_id = get_user_id_from_token(token)

    mongo_db["followers"].update_one(
        {"user_id": user_id},
        {"$pull": {"follows": target_id}}
    )
    return {"message": f"Unfollowed {target_id}"}

@router.get("/suggested")
def get_suggested_users(token: str = Query(...)):
    current_user = get_user_id_from_token(token)

    all_users = mongo_db["users"].find({"_id": {"$ne": ObjectId(current_user)}})
    follow_doc = mongo_db["followers"].find_one({"user_id": current_user})
    following = follow_doc.get("follows", []) if follow_doc else []

    suggestions = []
    for user in all_users:
        suggestions.append({
            "user_id": str(user["_id"]),
            "username": user["username"],
            "avatar_url": user.get("avatar_url"),
            "is_following": str(user["_id"]) in following
        })

    return suggestions
