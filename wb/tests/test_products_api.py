import types

import requests

from wb.api.products_api import (
    check_connection,
    _get_response_from_card_list_endpoint,
    get_products_list
)
from wb.consts import AUTHORIZATION_TOKEN


s = requests.Session()
s.headers.update({
    "Authorization": AUTHORIZATION_TOKEN,
    "Content-Type": "application/json",
})

def test_check_connection():
    assert check_connection(session=s), "проверка подключения должна возвращать True"

def test_get_response_from_card_list_endpoint():
    response_data = _get_response_from_card_list_endpoint(
        session=s,
        offset=0,
        limit=1
    )
    assert response_data["result"]["cards"], "в ответе, должен быть обьект rusult со списком cards"

def test_get_products_list_returns_generator():
    products = get_products_list(session=s)
    assert isinstance(products, types.GeneratorType), "функция должна вернуть генератор"
