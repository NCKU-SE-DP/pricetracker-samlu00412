from sqlalchemy import Column,Integer,Table,ForeignKey
from src.database import Base

class Constants:
    MAX_USERNAME_LENGTH = 50
    MAX_PASSWORD_LENGTH = 200
    KEY = '1892dhianiandowqd0n'
    NEWS_LINK = "https://udn.com/api/more"
    LLM_MODEL = "gpt-3.5-turbo"
    PRICES_INFO = "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice"
    ID_START = 1000000
    ENCODING_ALGO="HS256"

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)