import math
import uuid
import datetime
from urllib.parse import urljoin

import requests
import pandas as pd


FBS_ORDERS_BASE_API = 'https://suppliers-orders.wildberries.ru'
FBS_ORDERS_STATUSES_BASE_API = 'https://marketplace-remotewh.wildberries.ru'
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
        /card/list/ API-эндпоинта suppliers-api.wildberries.ru и,
        /api/v1/supplier/orders API-эндпоинта suppliers-stats.wildberries.ru и,
        /api/v1/supplier/reportDetailByPeriod API-эндпоинта https://suppliers-orders.wildberries.ru и
        /api/public/v1/supply_tasks/status API-эндпоинта https://marketplace-remotewh.wildberries.ru.
    """
    session = _get_session_for_content_api(authorization_token=access['CONTENT_API_AUTHORIZATION_TOKEN'])
    content_api_response = session.post(
        url=urljoin(CONTENT_BASE_API, '/card/list'),
        json=_get_product_list_request_data(
            supplier_id=access['SUPPLIER_ID'], offset=0, limit=1)
    )
    fbs_orders_api_response = requests.get(
        url=urljoin(FBS_ORDERS_BASE_API, '/api/v1/orders'),
        params={
            'date_start': datetime.datetime.now().isoformat() + ORDERS_API_TZ,  # приведение времени к таймзоне WB
            'date_end': datetime.datetime.now().isoformat() + ORDERS_API_TZ
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )
    fbs_orders_statuses_api_response = requests.get(
        url=urljoin(FBS_ORDERS_STATUSES_BASE_API, '/api/public/v1/supply_tasks/status'),
        params={
            'date_start': datetime.datetime.now().isoformat() + ORDERS_API_TZ,  # приведение времени к таймзоне WB
            'date_end': datetime.datetime.now().isoformat() + ORDERS_API_TZ
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )
    sales_api_response = requests.get(
        url=urljoin(STATISTICS_BASE_API, '/api/v1/supplier/reportDetailByPeriod'),
        params={
            'key': access['STATISTICS_API_KEY'],
            'dateFrom': datetime.datetime.now().isoformat(),
            'dateTo': datetime.datetime.now().isoformat()
        }
    )

    return (content_api_response.status_code
            and fbs_orders_api_response.status_code
            and fbs_orders_statuses_api_response.status_code
            and sales_api_response.status_code == requests.codes.ok)


def product_list(access, page_size=50):
    """Получение генератора с "сырыми" данными товаров в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.
            Аргументы:
                access (dict): Словарь с данными для авторизации в API.
                page_size (int): Максимальное количество карточек товаров,
                                 которые надо вывести.
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
                supplier_id=access['SUPPLIER_ID'],
                offset=page * page_size, limit=page_size)
        ).json()

        if not 'result' in response_data:
            yield from ()

        products = response_data['result']['cards']
        for product in products:
            yield product


def fbs_order_list(access, from_datetime, to_datetime):
    """Получение генератора с "сырыми" данными заказов поставщика в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.
            Аргументы:
                access (dict): Словарь с данными для авторизации в API.
                from_datetime (datetime): Конкретная дата с которой выгружать заказы.
                to_datetime (datetime): Конкретная дата по которую выгружать заказы.
            Возвращает:
                order (json): Генератор.
    """
    response = requests.get(
        url=urljoin(FBS_ORDERS_BASE_API, '/api/v1/orders'),
        params={
            'date_start': from_datetime.isoformat() + ORDERS_API_TZ,  # приведение времени к таймзоне WB
            'date_end': to_datetime.isoformat() + ORDERS_API_TZ
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )

    if response.status_code != requests.codes.ok:
        yield from ()

    response_data = response.json()

    for order in response_data:
        order['rid'] = int(order['items'][0]['rid'])
        yield order
    else:
        yield from ()


def statistics_sales_list(access, from_datetime):
    """Получение генератора с "сырыми" данными продаж в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.
       Выгружает продажи с переданной даты по сегодняшний день.
            Параметры:
                access (dict): Словарь с данными для авторизации в API.
                from_datetime (datetime): Конкретная дата с которой выгружать продажи.
            Возвращает:
                order (json): Генератор.
    """
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


def fbs_orders_statuses_list(access, from_datetime, to_datetime):
    response = requests.get(
        url=urljoin(FBS_ORDERS_STATUSES_BASE_API, '/api/public/v1/supply_tasks/status'),
        params={
            'date_start': from_datetime.isoformat() + ORDERS_API_TZ,  # приведение времени к таймзоне WB
            'date_end': to_datetime.isoformat() + ORDERS_API_TZ
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )

    if response.status_code != requests.codes.ok:
        yield from ()

    response_data = response.json()

    for order in response_data:
        order = {
            'order_id': order['order_id'],
            'last_status': order['items'][-1]['status']
        }
        yield order
    else:
        yield from ()


def order_list(access, from_datetime, to_datetime):
    """Получение генератора с "сырыми" данными заказов,
       сопоставленных с продажими и статусами заказов в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.
            Параметры:
                access (dict): Словарь с данными для авторизации в API.
                from_datetime (datetime): Конкретная дата с которой выгружать продажи.
                to_datetime (datetime): Конкретная дата по которую выгружать заказы.
            Возвращает:
                order (json): Генератор.
    """
    orders_df = pd.DataFrame.from_records(
        fbs_order_list(access=access, from_datetime=from_datetime, to_datetime=to_datetime)
    )
    sales_df = pd.DataFrame.from_records(
        statistics_sales_list(access=access, from_datetime=from_datetime)
    )
    orders_statuses_df = pd.DataFrame.from_records(
        fbs_orders_statuses_list(access=access, from_datetime=from_datetime,
                                 to_datetime=to_datetime)
    )
    orders = pd.merge(orders_df, sales_df, on='rid').merge(
        orders_statuses_df, on='order_id').to_dict(orient='records')

    for order in orders:
        yield order