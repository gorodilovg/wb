import math
import uuid
import datetime
from urllib.parse import urljoin
from json.decoder import JSONDecodeError
import itertools

import requests
import dateutil.parser


FBS_ORDERS_BASE_API = 'https://suppliers-orders.wildberries.ru'
STATISTICS_BASE_API = 'https://suppliers-stats.wildberries.ru'
CONTENT_BASE_API = 'https://suppliers-api.wildberries.ru'
ORDERS_API_TZ = "+03:00"

def _get_session_for_content_api(authorization_token):
    """Возвращает обьект сессии для работы с Content API."""
    session = requests.Session()
    session.headers.update({
        'Authorization': authorization_token,
        'Content-Type': 'application/json',
    })
    return session


def _get_product_list_request_data(supplier_id, offset, limit):
    """Формирование начальных данных
       для получения карточек товаров Content API.
    """
    return {
        'jsonrpc': '2.0',
        'id': str(uuid.uuid4()),
        'params': {
            'supplierID': supplier_id,
            'query': {
                'offset': offset,
                'limit': limit
            }
        }
    }

def check_connection(access):
    """Проверка работы
        /card/list/ API-эндпоинта suppliers-api.wildberries.ru и
        /api/v1/supplier/orders API-эндпоинта suppliers-stats.wildberries.ru.
    """
    session = _get_session_for_content_api(authorization_token=access['CONTENT_API_AUTHORIZATION_TOKEN'])

    content_api_response = session.post(
        url=urljoin(CONTENT_BASE_API, '/card/list'),
        json=_get_product_list_request_data(supplier_id=access['SUPPLIER_ID'], offset=0, limit=1))
    statistics_api_response = requests.get(
        url=urljoin(STATISTICS_BASE_API, '/api/v1/supplier/orders'),
        params={
            'key': access['API_KEY'],
            'dateFrom': datetime.datetime.now()
        }
    )

    return (content_api_response.status_code
            and statistics_api_response.status_code == requests.codes.ok)


def product_list(access, page_size=50):
    """Получение генератора с "сырыми" данными товаров в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.
            Аргументы:
                page_size (int): Максимальное количество карточек товаров, которые надо вывести.

            Возвращает:
                product (json): Генератор.
    """
    session = _get_session_for_content_api(authorization_token=access['CONTENT_API_AUTHORIZATION_TOKEN'])

    response = session.post(
        url=urljoin(CONTENT_BASE_API, '/card/list'),
        json=_get_product_list_request_data(supplier_id=access['SUPPLIER_ID'], offset=0, limit=1)
    )

    if response.status_code != requests.codes.ok:
        yield from ()

    response_data = response.json()

    if not 'result' in response_data:
        yield from ()

    total_products = response_data['result']['cursor']['total']

    for page in range(0, math.ceil(total_products / page_size)):

        response_data = session.post(
            url=urljoin(CONTENT_BASE_API, '/card/list'),
            json=_get_product_list_request_data(
                supplier_id=access['SUPPLIER_ID'], offset=page * page_size, limit=page_size)
        ).json()

        if not 'result' in response_data:
            yield from ()

        products = response_data['result']['cards']
        for product in products:
            yield product


def fbs_order_list(access, from_datetime, to_datetime):
    """Получение генератора с "сырыми" данными заказов поставщика в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.

            Параметры:
                from_datetime (datetime): Конкретная дата с которой выгружать заказы.
                to_datetime (datetime): Конкретная дата по которую выгружать заказы.
            Возвращает:
                order (json): Генератор.
    """
    response = requests.get(
        url=urljoin(FBS_ORDERS_BASE_API, '/api/v1/orders'),
        params={
            'date_start': from_datetime.isoformat() + ORDERS_API_TZ,
            'date_end': to_datetime.isoformat() + ORDERS_API_TZ
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )

    if response.status_code != requests.codes.ok:
        yield from ()

    response_data = response.json()

    for order in response_data:
        yield order
    else:
        yield from ()


def statistics_sales_list(access, from_datetime):

    response = requests.get(
        url=urljoin(STATISTICS_BASE_API, '/api/v1/supplier/reportDetailByPeriod'),
        params={
            'key': access['STATISTICS_API_KEY'],
            'dateFrom': from_datetime.isoformat(),
            'dateTo': datetime.datetime.now().isoformat()
        }
    )

    if response.status_code != requests.codes.ok:
        yield from ()

    response_data = response.json()

    for sale in response_data:
        yield sale
    else:
        yield from ()


# order
# {
#     "date_created": "2021-04-10T08:49:56.713175+03:00",
#     "items": [
#       {
#         "rid": "50418284378"
#          ...
#       },
#       {
#         "rid": "60318284378"
#          ...
#       },
# }

# sale
# {
#     "rid": 50406899506
# }

# В заказе может быть несколько вещей
# Если вещей несколько - то для каждой вещи должна быть одна продажа
# На основе продаж сформировать список заказов
# Наверное каждой вещи соответсвует одна продажа


def order_list(access, from_datetime, to_datetime):
    orders = fbs_order_list(access=access, from_datetime=from_datetime, to_datetime=to_datetime)
    sales = list(statistics_sales_list(access=access, from_datetime=from_datetime))

    orders_rids = [
        int(item["rid"]) for item in itertools.chain.from_iterable(
            order["items"] for order in orders)
    ]

    sales_rids = [sale["rid"] for sale in sales]

    existing_sales_rids = [sales_rid for sales_rid in sales_rids if sales_rid in orders_rids]

    for sale in sales:
        if sale["rid"] in existing_sales_rids:
            yield sale