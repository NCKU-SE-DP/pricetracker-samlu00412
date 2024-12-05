import json
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from openai import OpenAI
from src.configs import Constants,user_news_association_table
from src.posts.models import NewsArticle
from src.crawler.udn_crawler import UDNCrawler
from src.crawler.crawler_base import Headline
from src.llm_client.openai_client import OpenAIClient

id_counter = itertools.count(start=Constants.ID_START)
crawler = UDNCrawler()
ChatGPT = OpenAIClient(api_key=Constants.API_KEY)


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
        all_news_data = crawler.get_headline(search_term,page=Constants.INIT_PAGE_NUM)
    return all_news_data

# add new to database
def add_new(news_data):
    crawler.save(news=news_data)
    
def get_new(is_initial=False):
    news_data = get_new_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news.title
        relevance = ChatGPT.evaluate_relevance(title)

        if relevance == "high":
            summarize_new(news)
            
def summarize_new(news: Headline):
    detailed_news = crawler.parse(news["titleLink"])
    result = ChatGPT.generate_summary(" ".join(detailed_news["content"]))
    result = json.loads(result)
    detailed_news["summary"] = result["影響"]
    detailed_news["reason"] = result["原因"]
    add_new(detailed_news)


# Update the number of likes
def toggle_upvote(article_id, user_id, database):
    existing_upvote = database.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == article_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == article_id,
            user_news_association_table.c.user_id == user_id,
        )
        database.execute(delete_stmt)
        database.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=article_id, user_id=user_id
        )
        database.execute(insert_stmt)
        database.commit()
        return "Article upvoted"
    
    
def news_exists(id2, database: Session):
    return database.query(NewsArticle).filter_by(id=id2).first() is not None
