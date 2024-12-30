"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news articles from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news articles based on a search term,
parse the details of individual articles, and save them to a database using SQLAlchemy ORM.

Classes:
    UDNCrawler: A class to scrape news from UDN.

Exceptions:
    DomainMismatchException: Raised when the URL domain does not match the expected domain for the crawler.

Usage Example:
    crawler = UDNCrawler(timeout=10)
    headlines = crawler.startup("technology")
    for headline in headlines:
        news = crawler.parse(headline.url)
        crawler.save(news, db_session)

UDNCrawler Methods:
    __init__(self, timeout: int = 5): Initializes the crawler with a default timeout for HTTP requests.
    startup(self, search_term: str) -> list[Headline]: Fetches news headlines for a given search term across multiple pages.
    get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]: Fetches news headlines for specified pages.
    _fetch_news(self, page: int, search_term: str) -> list[Headline]: Helper method to fetch news headlines for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
    _parse_headlines(response): Parses the response to extract headlines.
    parse(self, url: str) -> News: Parses a news article from a given URL.
    _extract_news(soup, url: str) -> News: Extracts news details from the BeautifulSoup object.
    save(self, news: News, db: Session): Saves a news article to the database.
    _commit_changes(db: Session): Commits the changes to the database with error handling.
"""

from requests import Response,get
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sentry_sdk import capture_exception
from urllib.parse import quote
import logging

from src.crawler.crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary
from src.crawler.exceptions import DomainMismatchException,ExtractionException,ParseException
from src.posts.models import NewsArticle

class UDNCrawler(NewsCrawlerBase):
    CHANNEL_ID = 2
    NEWS_WEBSITE_URL = "https://udn.com/api/more"
    NEWS_WEBSITE_NEWS_CHILD_URLS = []

    def __init__(self, timeout: int = 5) -> None:
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Initializes the application by fetching news headlines for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches headlines from the first 10 pages.

        :param search_term: The term to search for in news headlines.
        :return: A list of Headline namedtuples containing the title and URL of news articles.
        :rtype: list[Headline]
        """
        return self.get_headlines(search_term, page=(1, 10))

    def get_headlines(
        self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:

        # Calculate the range of pages to fetch news from.
        # If 'page' is a tuple, unpack it and create a range representing those pages (inclusive).
        # If 'page' is an int, create a list containing only that single page number.
        # page_range = range(*page) if isinstance(page, tuple) else [page]
        headlines = []
        if isinstance(page,tuple):
            page_range = range(page[0],page[1]+1)
        else:
            page_range = [page]
        for num in page_range:
            headlines.extend(self._fetch_headlines(num,search_term))
        return headlines

    def _fetch_headlines(self, page: int, search_term: str) -> list[Headline]:
        response = self._perform_request(self.NEWS_WEBSITE_URL,
                                         self._create_search_params(page, search_term, "searchword"))
        return self._parse_headlines(response)

    def _create_search_params(self, page: int, search_term: str, type: str = "searchword") -> dict:
        return {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": self.CHANNEL_ID,
            "type": type,
        }

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        return get(url, params, timeout=self.timeout)
            

    @staticmethod
    def _parse_headlines(response: Response) -> list[Headline]:
        news_list = response.json()["lists"]
        processed_headlines_list = []
        for news in news_list:
            headline = Headline(title=news["title"], url=news["titleLink"])
            processed_headlines_list.append(headline)
        return processed_headlines_list

    def parse(self, url: str) -> News:
        response = self._perform_request(url)
        if not self._is_valid_url(url):
            raise DomainMismatchException(url)
        try:
            return self._extract_news(BeautifulSoup(response.text, "html.parser"), url)
        except Exception as e:
            logging.error(f"[UDNCrawler] Error parsing news content: {e}")
            raise ParseException(url)

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        try:
            title = soup.find("h1", class_="article-content__title").text
            content_time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")
            paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]

            return News(
                url=url,
                title=title,
                time=content_time,
                content=" ".join(paragraphs)
            )
        except Exception as e:
            logging.error(f"[UDNCrawler] Error extracting news content: {e}")
            raise ExtractionException(url)


    def save(self, news: NewsWithSummary, database: Session):
        database.add(news)
        self._commit_changes(database)
        

    @staticmethod
    def _commit_changes(database: Session):
        try:
            database.commit()
        except Exception as error:
            logging.error(f"[UDNCrawler] Failed to save news to database: {error}")
            capture_exception(error)
            database.rollback()
        database.close()
            
