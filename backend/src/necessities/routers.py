from fastapi import APIRouter,Query
import requests

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
    return requests.get(
        Constants.Link.PRICES_INFO_LINK,
        params={"CategoryName": category, "Name": commodity}
    ).json()
