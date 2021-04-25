import datetime
import time
import itertools

import dateutil.parser

from wb.consts import (
    CONTENT_API_AUTHORIZATION_TOKEN, SUPPLIER_ID,
    STATISTICS_API_KEY, ORDERS_API_TOKEN
)
from wb.api import check_connection, product_list, fbs_order_list, statistics_sales_list, order_list


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


def test_order_list_returns_true_date_range_orders():
    time.sleep(60)
    from_datetime = datetime.datetime(year=2021, month=4, day=1)
    to_datetime = datetime.datetime(year=2021, month=4, day=23)
    orders = list(
        sorted(
            fbs_order_list(access=ACCESS, from_datetime=from_datetime, to_datetime=to_datetime),
            key=lambda order: dateutil.parser.parse(order["date"])
        )
    )

    first_order_datetime = dateutil.parser.parse(orders[0]["date"])
    last_order_datetime = dateutil.parser.parse(orders[-1]["date"])

    assert first_order_datetime < last_order_datetime
    assert last_order_datetime > first_order_datetime
    assert first_order_datetime >= from_datetime
    assert last_order_datetime <= to_datetime


from_datetime = datetime.datetime(year=2021, month=4, day=1)
to_datetime = datetime.datetime(year=2021, month=4, day=25)

# orders = fbs_order_list(access=ACCESS, from_datetime=from_datetime, to_datetime=to_datetime)
#
# orders = list(map(
#         lambda order: {
#             "date_created": order["date_created"],
#             "items": [item["rid"] for item in order["items"]]
#         },
#         sorted(
#             orders,
#             key=lambda order: dateutil.parser.parse(order["date_created"])
#         )
#     )
# )
# orders_rids = list(map(int, itertools.chain.from_iterable(order["items"] for order in orders)))
#
# sales = statistics_sales_list(ACCESS, from_datetime=from_datetime)
#
# sales = list(map(
#         lambda sale: {
#             "order_dt": sale["order_dt"],
#             "sale_dt": sale["sale_dt"],
#             "rid": sale["rid"]
#         },
#         sorted(
#             sales,
#             key=lambda sale: dateutil.parser.parse(sale["order_dt"])
#         )
#     )
# )
# sales_rids = list(sale["rid"] for sale in sales)
#
# matches = []
#
# for sale in sales_rids:
#     if sale in orders_rids:
#         matches.append(sale)
#
#
# # orders = fbs_order_list(access=ACCESS, from_datetime=from_datetime, to_datetime=to_datetime)
# # sales = statistics_sales_list(access=ACCESS, from_datetime=from_datetime)


orders = list(order_list(ACCESS, from_datetime, to_datetime))


print()