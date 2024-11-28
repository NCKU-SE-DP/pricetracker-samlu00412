from fastapi import APIRouter,Depends
from openai import OpenAI
import json

from src.configs import Constants
from src.database import session_opener
from src.posts.models import NewsArticle
from src.auth.depends import authenticate_user_token
from src.posts.depends import get_article_upvote_details,get_new_info,toggle_upvote,id_counter
from src.posts.schemas import PromptRequest,NewsSumaryRequestSchema

from src.crawler.udn_crawler import UDNCrawler


router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404:{"Description" : "Not found"}}
)
crawler = UDNCrawler()

@router.get("/news") 
def read_news(database=Depends(session_opener)):
    """Read new's information, number of likes, and whether the news is liked by people, and return it."""
    news = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for new in news: 
        likes, is_liked = get_article_upvote_details(new.id, None, database)
        result.append(
            {**new.__dict__, "upvotes": likes, "is_upvoted": is_liked}
        )
    return result

@router.get("/user_news") 
def read_user_news(
        database=Depends(session_opener),
        user=Depends(authenticate_user_token)
):
    """Read news which user stored"""
    news = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        likes, is_liked = get_article_upvote_details(article.id, user.id, database)
        result.append(
            {**article.__dict__,"upvotes": likes,"is_upvoted": is_liked}
        )
    return result

@router.post("/search_news")
async def search_news(request: PromptRequest):
    """Input a prompt, and catch the data which AI finds."""
    news_list = []
    summary_prompt  = [{
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{request.prompt}"}
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model=Constants.LLM_MODEL,
        messages=summary_prompt
    )
    keywords = completion.choices[0].message.content
    # should change into simple factory pattern
    news_items = get_new_info(keywords, is_initial=False)
    for news in news_items:
        try:
            detailed_news = crawler.validate_and_parse(url=news.url)
            json = detailed_news.model_dump()
            json["id"] = next(id_counter)
            news_list.append(json)
        except Exception as error_message:
            print(error_message)
    return sorted(news_list, key=lambda time: time["time"], reverse=True)

@router.post("/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    """Input a prompt, and make a summary of news."""
    response = {}
    summary_prompt = [{
            "role": "system",
            "content": Constants.GPT_SUMMARY_PROMPT
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model=Constants.LLM_MODEL,
        messages=summary_prompt ,
    )
    result = completion.choices[0].message.content
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

@router.post("/{id}/upvote")
def upvote_article(
        id,
        database=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    """Update the state of upvoted article"""
    message = toggle_upvote(id, user.id, database)
    return {"message": message}


