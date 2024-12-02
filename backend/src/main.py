from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

from src.posts.depends import get_new
from src.posts.models import NewsArticle
from src.posts.routers import router as news_router

from src.database import engine
from src.services import Background_scheduler

from src.users.routers import router as users_router

from src.necessities.routers import router as necessities_router


app = FastAPI()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.include_router(users_router,prefix="/api/v1")
app.include_router(news_router,prefix="/api/v1")
app.include_router(necessities_router,prefix="/api/v1")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def start_scheduler():
    database = SessionLocal()
    if database.query(NewsArticle).count() == 0:
        get_new()
    database.close()
    Background_scheduler.add_job(get_new, "interval", minutes=100)
    Background_scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    Background_scheduler.shutdown()
