from sqlalchemy import Column,Integer,Table,ForeignKey
from src.database import Base

class Constants:
    MAX_USERNAME_LENGTH = 50
    INIT_PAGE_NUM = 1
    MAX_PASSWORD_LENGTH = 200
    KEY = '1892dhianiandowqd0n'
    NEWS_LINK = "https://udn.com/api/more"
    LLM_MODEL = "gpt-3.5-turbo"
    PRICES_INFO = "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice"
    ID_START = 1000000
    ENCODING_ALGO="HS256"
    GPT_SUMMARY_PROMPT = "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})"
    GPT_RELEVANCE_PROMPT = "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)"

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)