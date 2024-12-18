from fastapi import APIRouter,Depends,HTTPException
from sentry_sdk import capture_exception
from typing import Union
import logging

from src.database import session_opener
from src.llm_client.exceptions import EvaluationFailure
from src.posts.models import NewsArticle
from src.auth.depends import authenticate_user_token
from src.posts.services import get_article_upvote_details,get_new_info,toggle_upvote,id_counter,openai,anthropic
from src.posts.schemas import PromptRequest,NewsSumaryRequestSchemaWithModel,NewsSummaryRequestSchema
from src.crawler.udn_crawler import UDNCrawler
from src.error_handlers.llm_exception import InvalidModelError,NoPromptError



router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404:{"Description" : "Not found"}}
)
crawler = UDNCrawler()


@router.get("/news") 
def read_news(database=Depends(session_opener)):
    """Read new's information, number of likes, and whether the news is liked by people, and return it."""
    logging.debug("Accessed /api/v1/news/news")
    try:
        news = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except Exception as err:
        logging.error(f"Failed to fetch news: {err}")
        capture_exception(err)
        return HTTPException(status_code=400, detail="Failed to fetch news")
    result = []
    for new in news: 
        try:
            likes, is_liked = get_article_upvote_details(new.id, None, database)
        except Exception as err:
            logging.warning(f"Failed to fetch upvote details for news '{new.id}': {err}, skipping.")
            capture_exception(err)
            continue
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
    logging.debug(f"{user.id} accessed /api/v1/news/user_news")
    try:
        news = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except Exception as err:
        logging.error(f"Failed to fetch news: {err}")
        capture_exception(err)
        return HTTPException(status_code=400, detail="Failed to fetch news")
    result = []
    for article in news:
        try:
            likes, is_liked = get_article_upvote_details(article.id, user.id, database)
        except Exception as err:
            logging.warning(f"Failed to fetch upvote details for news '{article.id}': {err}, skipping.")
            capture_exception(err)
            continue
        result.append(
            {**article.__dict__,"upvotes": likes,"is_upvoted": is_liked}
        )
    return result

@router.post("/search_news")
async def search_news(request: PromptRequest):
    """Input a prompt, and catch the data which AI finds."""
    logging.debug(f"Accessed /api/v1/news/search_news: {request.prompt}")
    if request.prompt == "":
        raise NoPromptError()
    prompt = request.prompt
    news_list = []
    try:
        keywords = openai.extract_search_keywords(request.prompt)
    except Exception as err:
        logging.error(f"Failed to extract search keywords: {err}")
        capture_exception(err)
        return HTTPException(status_code=400, detail="Something went wrong while processing search keywords")
    # should change into simple factory pattern
    try:
        news_items = get_new_info(keywords, is_initial=False)
    except Exception as err:
        logging.error(f"Failed to fetch news info: {err}")
        capture_exception(err)
        return HTTPException(status_code=400, detail="Failed to fetch news info")
    
    for news in news_items:
        try:
            detailed_news = crawler.validate_and_parse(url=news.url)
        except Exception as err:
            logging.error(f"Failed to validate and parse news: {err}")
            capture_exception(err)
            continue
        detailed_news.id = next(id_counter)
        news_list.append(detailed_news)
        
    return sorted(news_list, key=lambda time: time["time"], reverse=True)

async def _generate_summary(
        payload: Union[NewsSumaryRequestSchemaWithModel,NewsSummaryRequestSchema], user=Depends(authenticate_user_token), llm_model="openai"
):
    response = {}

    try:
        if not llm_model:
            return HTTPException(status_code=400, detail="Model is required")
        elif llm_model.lower() == "openai":
            result = openai.generate_summary(payload.content)
        elif llm_model.lower() == "anthropic" or llm_model.lower() == "claude":
            result = anthropic.generate_summary(payload.content)
        else:
            return HTTPException(status_code=400, detail="Invalid model")
    except EvaluationFailure as e:
        logging.error(f"Failed to generate summary: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to generate summary")
    

    if result:
        try:
            response["summary"] = result["影響"]
            response["reason"] = result["原因"]
        except KeyError as e:
            logging.error(f"Failed to extract summary and reason as format returned from LLM is incorrect: {e}")
            capture_exception(e)
            return HTTPException(status_code=400, detail="Something went wrong while processing summary")
    return response

@router.post("/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchemaWithModel, user=Depends(authenticate_user_token)
):
    """Input a prompt, and make a summary of news."""
    return await _generate_summary(payload, user)

@router.post("/news_summary_with_custom_model")
async def news_summary_with_custom_model(
        payload: NewsSumaryRequestSchemaWithModel, user=Depends(authenticate_user_token)
):
    return await _generate_summary(payload, user, payload.ai_model)

@router.post("/{id}/upvote")
def upvote_article(
        id,
        database=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    """Update the state of upvoted article"""
    logging.debug(f"{user.id} accessed /api/v1/news/{id}/upvote")
    message = toggle_upvote(id, user.id, database)
    return {"message": message}


