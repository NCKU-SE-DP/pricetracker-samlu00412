from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

from src.posts.services import get_new
from src.posts.models import NewsArticle
from src.posts.routers import router as news_router
from src.error_handlers.server_exception import InternalServerError
from src.database import engine
from src.services import Background_scheduler

from src.users.routers import router as users_router

from src.prices.routers import router as pricess_router
from src.util import init_logger
import logging
init_logger()
logging.debug("Initialisation started.")


app = FastAPI()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.include_router(users_router,prefix="/api/v1")
logging.debug("News router (/news) initialised")
app.include_router(news_router,prefix="/api/v1")
logging.debug("Users router (/router) initialised")
app.include_router(pricess_router,prefix="/api/v1")
logging.debug("Prices router (/prices) initialised")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def start_scheduler():
    try:
        database = SessionLocal()
        if database.query(NewsArticle).count() == 0:
            logging.info("No news present in the database. Fetching latest news.")
            get_new()
        database.close()
        Background_scheduler.add_job(get_new, "interval", minutes=100)
        Background_scheduler.start()
        logging.debug("Background scheduler started.")
        logging.info("PriceTracker backend has started.")
    except Exception as err:
        raise InternalServerError(err)

@app.on_event("shutdown")
def shutdown_scheduler():
    Background_scheduler.shutdown()
    logging.debug("Background scheduler shutdown.")