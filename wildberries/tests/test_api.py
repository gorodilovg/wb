import datetime

from pytz import timezone

from wildberries.consts import (
    CONTENT_API_AUTHORIZATION_TOKEN, SUPPLIER_ID,
    STATISTICS_API_KEY, ORDERS_API_TOKEN
)
from wildberries.api import check_connection, product_list, fbs_order_list


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
    tz = timezone('UTC')
    from_datetime = tz.localize(datetime.datetime(year=2021, month=4, day=1))
    to_datetime = tz.localize(datetime.datetime(year=2021, month=4, day=30))
    orders = fbs_order_list(ACCESS, from_datetime, to_datetime)
    assert list(orders), "функция должна вернуть не пустой список заказов"


tz = timezone('UTC')
from_datetime = tz.localize(datetime.datetime(year=2021, month=4, day=1))
to_datetime = tz.localize(datetime.datetime(year=2021, month=5, day=1))
orders = list(fbs_order_list(ACCESS, from_datetime, to_datetime))
# products = list(product_list(ACCESS))

print()