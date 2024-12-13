from fastapi import APIRouter,Depends

from src.database import session_opener
from src.posts.models import NewsArticle
from src.auth.depends import authenticate_user_token
from src.posts.depends import get_article_upvote_details,get_new_info,toggle_upvote,id_counter,openai,anthropic
from src.posts.schemas import PromptRequest,NewsSumaryRequestSchemaWithModel
from src.crawler.udn_crawler import UDNCrawler
from src.llm_client.openai_client import OpenAIClient
from src.configs import Constants


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
    keywords = openai.extract_search_keywords(request.prompt)

    # should change into simple factory pattern
    news_items = get_new_info(keywords, is_initial=False)
    for news in news_items:
        try:
            detailed_news = crawler.validate_and_parse(url=news.url)
            json = detailed_news.model_dump()
            json["id"] = next(id_counter)
            news_list.append(json)
            detailed_news = crawler.validate_and_parse(url=news.url)
            json = detailed_news.model_dump()
            json["id"] = next(id_counter)
            news_list.append(json)
        except Exception as error_message:
            print(error_message)
    return sorted(news_list, key=lambda time: time["time"], reverse=True)

@router.post("/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchemaWithModel, user=Depends(authenticate_user_token)
):
    """Input a prompt, and make a summary of news."""
    response = {}
    result = openai.generate_summary(payload.content)

    if result:
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

@router.post("/news_summary_with_custom_model")
async def news_summary_with_custom_model(
        payload: NewsSumaryRequestSchemaWithModel, user=Depends(authenticate_user_token)
):
    response = {}

    if not payload.ai_model:
        return {"message": "Please select a model."}
    elif payload.ai_model.lower() == "openai":
        result = openai.generate_summary(payload.content)
    elif payload.ai_model.lower() == "anthropic" or payload.ai_model.lower() == "claude":
        result = anthropic.generate_summary(payload.content)
    else:
        return {"message": "Invalid model."}
    
    if result:
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


