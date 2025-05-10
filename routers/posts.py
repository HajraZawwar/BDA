from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from jose import jwt, JWTError
from database import mongo_db, s3_client
import uuid
import config
from fastapi import Query
from fastapi import Path
from bson import ObjectId

router = APIRouter()

# Auth utility
def get_user_id_from_token(token: str = Form(...)) -> str:
    try:
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Upload Post Route
@router.post("/upload")
async def upload_post(
    token: str = Form(...),
    caption: str = Form(...),
    image: UploadFile = File(...)
):
    user_id = get_user_id_from_token(token)

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Upload to S3
    key = f"posts/{uuid.uuid4()}.jpg"
    s3_client.upload_fileobj(image.file, config.S3_BUCKET_NAME, key)
    image_url = f"https://{config.S3_BUCKET_NAME}.s3.amazonaws.com/{key}"

    # Save post to MongoDB
    post = {
        "user_id": user_id,
        "caption": caption,
        "image_url": image_url,
        "likes": [],
        "comments": [],
        "created_at": datetime.utcnow()
    }

    mongo_db["posts"].insert_one(post)
    return JSONResponse(content={"message": "Post uploaded successfully", "image_url": image_url})


@router.get("/feed")
def get_feed(token: str = Query(...)):
    user_id = get_user_id_from_token(token)

    # Get list of people the user follows
    follow_doc = mongo_db["followers"].find_one({"user_id": user_id})
    following = follow_doc["follows"] if follow_doc else []

    # Include user's own posts
    following.append(user_id)

    # Fetch posts
    posts_cursor = mongo_db["posts"].find(
        {"user_id": {"$in": following}}
    ).sort("created_at", -1)

    posts = []
    for post in posts_cursor:
        posts.append({
            "username": mongo_db["users"].find_one({"_id": ObjectId(post["user_id"])})["username"],
            "caption": post["caption"],
            "image_url": post["image_url"],
            "likes": len(post["likes"]),
            "comments": post["comments"],
            "created_at": post["created_at"].isoformat()
        })

    return posts

@router.post("/{post_id}/like")
def like_post(post_id: str = Path(...), token: str = Form(...)):
    user_id = get_user_id_from_token(token)

    post = mongo_db["posts"].find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if user_id in post["likes"]:
        mongo_db["posts"].update_one({"_id": ObjectId(post_id)}, {"$pull": {"likes": user_id}})
        return {"message": "Post unliked"}
    else:
        mongo_db["posts"].update_one({"_id": ObjectId(post_id)}, {"$addToSet": {"likes": user_id}})
        return {"message": "Post liked"}


@router.post("/{post_id}/comment")
def comment_post(
    post_id: str = Path(...),
    token: str = Form(...),
    comment: str = Form(...)
):
    user_id = get_user_id_from_token(token)
    user = mongo_db["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    comment_doc = {
        "user_id": user_id,
        "username": user["username"],
        "text": comment,
        "timestamp": datetime.utcnow()
    }

    mongo_db["posts"].update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"comments": comment_doc}}
    )

    return {"message": "Comment added"}
