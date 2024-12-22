import json
import itertools
import logging
from sentry_sdk import capture_exception
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from src.configs import Constants,user_news_association_table
from src.posts.models import NewsArticle
from src.crawler.udn_crawler import UDNCrawler
from src.crawler.crawler_base import Headline,NewsWithSummary
from src.llm_client.openai_client import OpenAIClient
from backend.src.llm_client.anthropic_client import AnthropicClient
from src.llm_client.exceptions import EvaluationFailure

id_counter = itertools.count(start=Constants.News.ID_START)
crawler = UDNCrawler()

openai = OpenAIClient(api_key=Constants.APIKey.OPENAI_TOKEN)
anthropic = AnthropicClient(api_key=Constants.APIKey.ANTHROPIC_TOKEN)

def import_news(news_data: NewsWithSummary):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    crawler.save(news_data, session)

def get_article_upvote_details(article_id, user_id, database):
    num_of_likes = (
        database.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    is_liked = False
    if user_id:
        is_liked = (
                database.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
        )
    return num_of_likes, is_liked

# get news' information according to search_term, and return the data which the function found.
def get_new_info(search_term, is_initial=False):
    # iterate pages to get more news data, not actually get all news data
    # return crawler.get_headline(search_term, (1, 10) if is_initial else 1)
    if is_initial:
        all_news_data = crawler.startup(search_term=search_term)
    else:
        all_news_data = crawler.get_headline(search_term,page=Constants.News.INIT_PAGE_NUM)
    return all_news_data

# add new to database
def add_new(news_data):
    crawler.save(news=news_data)
    
def get_new(is_initial=False):
    news_data = get_new_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news.title
        try:
            relevance = openai.evaluate_relevance(title, "民生用品的價格變化")
        except EvaluationFailure as e:
            logging.error(f"Failed to evaluate relevance: {e}")
            capture_exception(e)
            return
        relevance = openai.evaluate_relevance(title)

        if relevance == "high":
            try:
                detailed_news = crawler.validate_and_parse(news.url)
            except Exception as e:
                logging.warning(f"Failed to validate and parse news for {news.title}: {e}, skipping")
                capture_exception(e)
                continue
            if detailed_news is None:
                continue

            try:
                result = openai.generate_summary(" ".join(detailed_news.content))
            except EvaluationFailure as e:
                logging.warning(f"Failed to generate summary for news {news.title}: {e}, skipping.")
                capture_exception(e)
                continue
            detailed_news = NewsWithSummary(
                url=detailed_news.url,
                title=detailed_news.title,
                time=detailed_news.time,
                content=detailed_news.content,
                summary=result["影響"],
                reason=result["原因"],
            )
            import_news(detailed_news)
        
    
def toggle_upvote(news_id, user_id, db):
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_command = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        db.execute(delete_command)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Failed to remove upvote: {e}")
            capture_exception(e)
            return "Failed to remove upvote"
        return "Upvote removed"
    else:
        insert_command = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        db.execute(insert_command)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Failed to upvote: {e}")
            capture_exception(e)
            return "Failed to upvote"
        return "Article upvoted"
    
def news_exists(news_id, database: Session):
    return database.query(NewsArticle).filter_by(id=news_id).first() is not None