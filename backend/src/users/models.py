from sqlalchemy import Column,Integer,String
from sqlalchemy.orm import relationship

from src.configs import Constants,user_news_association_table
from src.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(Constants.MAX_USERNAME_LENGTH), unique=True, nullable=False)
    hashed_password = Column(String(Constants.MAX_PASSWORD_LENGTH), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )
