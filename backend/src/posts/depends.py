import json
import itertools
from sqlalchemy import delete, insert, select
from openai import OpenAI
from sqlalchemy.orm import Session

from src.configs import Constants,user_news_association_table
from src.posts.models import NewsArticle
from src.crawler.udn_crawler import UDNCrawler as Crawl

id_counter = itertools.count(start=Constants.ID_START)

openai_client = OpenAI(api_key="")
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
    if is_initial:
        all_news_data = Crawl.startup(search_term=search_term)
    else:
        all_news_data = Crawl.get_headline(search_term=search_term,page=Constants.INIT_PAGE_NUM)
    return all_news_data

# add new to database
def add_new(news_data):
    Crawl.save(news=news_data)
    
"""
    get news and estimate the relavance.
    If relavance is high, function will make a summary
    
    The method have two functions, it should be splited (not split yet)
"""
def get_new(is_initial=False):
    news_data = get_new_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news["title"]
        GPTinfo = [{"role": "system","content": Constants.GPT_RELEVANCE_PROMPT},
                   {"role": "user", "content": f"{title}"}
                   ]
        ai = OpenAI(api_key="xxx").chat.completions.create(
            model= Constants.LLM_MODEL,
            messages=GPTinfo,
        )
        relevance = ai.choices[0].message.content
        if relevance == "high":
            detailed_news = Crawl.parse(news["titleLink"])
            GPTinfo = [{"role": "system","content": Constants.GPT_SUMMARY_PROMPT},
                       {"role": "user", "content": " ".join(detailed_news["content"])}
                       ]
            completion = OpenAI(api_key="xxx").chat.completions.create(
                model=Constants.LLM_MODEL,
                messages=GPTinfo,
            )
            result = completion.choices[0].message.content
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
