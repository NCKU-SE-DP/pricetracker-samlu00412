from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

from .posts.depends import get_new
from .posts.models import NewsArticle
from .posts.routers import router as news_router

from .database import engine
from .services import Background_scheduler

from .users.routers import router as users_router

from .necessities.routers import router as necessities_router


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

"""
get_new should change into simple factory pattern. (not yet)

the simple factory pattern as the following comment code.
"""
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

# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

