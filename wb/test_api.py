import datetime
import time

import dateutil.parser

from wb.consts import (
    CONTENT_API_AUTHORIZATION_TOKEN, SUPPLIER_ID,
    STATISTICS_API_KEY, ORDERS_API_TOKEN
)
from wb.api import check_connection, product_list, order_list


ACCESS = {
    "CONTENT_API_AUTHORIZATION_TOKEN": CONTENT_API_AUTHORIZATION_TOKEN,
    "SUPPLIER_ID": SUPPLIER_ID,
    "STATISTICS_API_KEY": STATISTICS_API_KEY,
    "ORDERS_API_TOKEN": ORDERS_API_TOKEN
}

def test_check_connection():
    assert check_connection(access=ACCESS), "проверка подключения должна возвращать True"


def test_get_products_list_returns_cards():
    products = product_list(access=ACCESS)
    assert list(products), "функция должна вернуть не пустой список товаров"


def test_order_list():
    from_datetime = datetime.datetime(year=2021, month=4, day=1)
    to_datetime = datetime.datetime(year=2021, month=4, day=25)
    orders = order_list(ACCESS, from_datetime, to_datetime)
    assert list(orders), "функция должна вернуть не пустой список заказов"


from_datetime = datetime.datetime(year=2021, month=4, day=17)
to_datetime = datetime.datetime(year=2021, month=4, day=19, hour=23, minute=59)
orders = list(
    sorted(
        order_list(ACCESS, from_datetime, to_datetime),
        key=lambda order: dateutil.parser.parse(order["date_created"])
    )
)

print()