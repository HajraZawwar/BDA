from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from routers import posts
from routers import users
from routers import chats


app = FastAPI(
    title="Instagram Lite",
    description="Scalable Social Media Platform",
    version="1.0.0"
)

# Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chats.router, prefix="/chat", tags=["Chat"])

@app.get("/")
def read_root():
    return {"message": "Instagram Lite API is running!"}
