import types
from datetime import datetime

import requests

from wb.api.orders_api import (
    check_connection,
    _get_response_from_orders_list_endpoint,
    get_orders_list
)


s = requests.Session()

def test_check_connection():
    assert check_connection(session=s), "проверка подключения должна возвращать True"

def test_get_response_from_card_list_endpoint():
    response_data = _get_response_from_orders_list_endpoint(
        session=s,
        from_datetime=datetime(year=2021, month=4, day=20))
    assert response_data, "в ответе, должен быть не пустой список заказов"

def test_get_orders_list_returns_generator():
    orders = get_orders_list(session=s, from_datetime=datetime(year=2021, month=4, day=20))
    assert isinstance(orders, types.GeneratorType), "функция должна вернуть генератор"
