import requests
import json
import itertools
from urllib.parse import quote
from sqlalchemy import delete, insert, select
from bs4 import BeautifulSoup
from openai import OpenAI
from sqlalchemy.orm import Session

from ..configs import Constants,user_news_association_table
from .models import NewsArticle

id_counter = itertools.count(start=Constants.ID_START)


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
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        news = []
        for page in range(1, 10):
            pageinfo = {
                "page": page,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get(Constants.NEWS_LINK, params=pageinfo)
            news.append(response.json()["lists"])

        for result in news:
            all_news_data.append(result)
    else:
        pageinfo = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get(Constants.NEWS_LINK, params=pageinfo)
        all_news_data = response.json()["lists"]
    return all_news_data

# add new to database
def add_new(news_data):
    session = Session()
    session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    session.commit()
    session.close()

"""
    get news and estimate the relavance.
    If relavance is high, function will make a summary
    
    The method have two functions, it should be splited (not split yet)
"""
def get_new(is_initial=False):
    news_data = get_new_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news["title"]
        GPTinfo = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{title}"},
        ]
        ai = OpenAI(api_key="xxx").chat.completions.create(
            model= Constants.LLM_MODEL,
            messages=GPTinfo,
        )
        relevance = ai.choices[0].message.content
        if relevance == "high":
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")
            paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "?" not in p.text
            ]
            detailed_news =  {
                "url": news["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            GPTinfo = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(detailed_news["content"])},
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
