from fastapi import APIRouter,Query,HTTPException
from sentry_sdk import capture_exception
import logging
import requests
from requests.exceptions import JSONDecodeError

from src.configs import Constants

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404:{"Description":"Not found"}}
)

@router.get("/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    try:
        return requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        ).json()
    except JSONDecodeError as e:
        logging.error(f"Failed to parse response: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Something went wrong while processing data")
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to fetch data")
    return requests.get(
        Constants.Link.PRICES_INFO_LINK,
        params={"CategoryName": category, "Name": commodity}
    ).json()
