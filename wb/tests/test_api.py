from uuid import uuid4
from urllib.parse import urljoin

import requests

from wb.api import check_connection
from wb.consts import AUTHORIZATION_TOKEN, SUPPLIER_ID


session = requests.Session()
session.headers.update({
    "Authorization": AUTHORIZATION_TOKEN,
    "Content-Type": "application/json",
})


def test_check_connection():
    assert check_connection(session=session), "проверка подключения должна возвращать True"


def test_product_list_response_integrity():
    initial_data = {
        "jsonrpc": "2.0",
        "id": str(uuid4()),
        "params": {
            "supplierID": f"{SUPPLIER_ID}",
            "query": {
                "limit": 1,
                "offset": 0
            }
        }
    }
    response_data = session.post(
        url=urljoin("https://suppliers-api.wildberries.ru", "/card/list"),
        json=initial_data
    ).json()

    assert response_data["result"]["cards"], "в ответе, должен быть обьект rusult со списком cards"