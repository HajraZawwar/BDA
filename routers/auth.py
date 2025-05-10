from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from bson import ObjectId
import uuid
import config
from database import mongo_db, s3_client
from models.user_model import UserCreate, UserLogin, Token
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Utility: Hash & verify password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# Utility: JWT Token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Signup Route
@router.post("/signup", response_model=dict)
async def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    avatar: UploadFile = File(None)
):
    user_collection = mongo_db["users"]

    if user_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    avatar_url = None
    if avatar:
        key = f"avatars/{uuid.uuid4()}.jpg"
        s3_client.upload_fileobj(avatar.file, config.S3_BUCKET_NAME, key)
        avatar_url = f"https://{config.S3_BUCKET_NAME}.s3.amazonaws.com/{key}"

    hashed_pwd = hash_password(password)
    user_doc = {
        "username": username,
        "email": email,
        "password": hashed_pwd,
        "avatar_url": avatar_url,
        "created_at": datetime.utcnow()
    }

    result = user_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # ✅ Auto-follow up to 3 existing users
    other_users = user_collection.find({"_id": {"$ne": result.inserted_id}}).limit(3)
    follows = [str(u["_id"]) for u in other_users]

    mongo_db["followers"].insert_one({
        "user_id": user_id,
        "follows": follows
    })

    return {"message": "User created", "user_id": user_id}

# Login Route
@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    user_collection = mongo_db["users"]
    db_user = user_collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token_data = {"sub": str(db_user["_id"])}
    token = create_access_token(token_data)
    return Token(access_token=token)
