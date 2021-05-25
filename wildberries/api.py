import datetime
import math
import uuid
from urllib.parse import urljoin

import requests
import pandas as pd
import simplejson
import dateutil.parser
from pytz import timezone


FBS_ORDERS_BASE_API = 'https://suppliers-orders.wildberries.ru'
FBS_ORDERS_STATUSES_BASE_API = 'https://marketplace-remotewh.wildberries.ru'
STATISTICS_BASE_API = 'https://suppliers-stats.wildberries.ru'
CONTENT_BASE_API = 'https://suppliers-api.wildberries.ru'


def _get_session_for_content_api(authorization_token):
    """
        Возвращает обьект сессии для работы с Content API.
    """
    session = requests.Session()
    session.headers.update({
        'Authorization': authorization_token,
        'Content-Type': 'application/json',
    })
    return session


def _get_product_list_request_data(supplier_id, offset, limit):
    """
        Формирование начальных данных
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
    """
        Проверка работы
        /card/list/ API-эндпоинта suppliers-api.wildberries.ru и,
        /api/v1/supplier/orders API-эндпоинта suppliers-stats.wildberries.ru и,
        /api/v1/supplier/reportDetailByPeriod API-эндпоинта https://suppliers-orders.wildberries.ru и
        /api/public/v1/supply_tasks/status API-эндпоинта https://marketplace-remotewh.wildberries.ru.
    """
    tz = timezone('UTC')
    session = _get_session_for_content_api(
        authorization_token=access['CONTENT_API_AUTHORIZATION_TOKEN']
    )
    content_api_response = session.post(
        url=urljoin(CONTENT_BASE_API, '/card/list'),
        json=_get_product_list_request_data(
            supplier_id=access['SUPPLIER_ID'], offset=0, limit=1)
    )
    fbs_orders_api_response = requests.get(
        url=urljoin(FBS_ORDERS_BASE_API, '/api/v1/orders'),
        params={
            'date_start': tz.localize(
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).isoformat(),
            'date_end': tz.localize(datetime.datetime.now()).isoformat()
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )
    fbs_orders_statuses_api_response = requests.get(
        url=urljoin(FBS_ORDERS_STATUSES_BASE_API, '/api/public/v1/supply_tasks/status'),
        params={
            'date_start': tz.localize(
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).isoformat(),
            'date_end': tz.localize(datetime.datetime.now()).isoformat()
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

    return (content_api_response.status_code == requests.codes.ok
            and fbs_orders_api_response.status_code == requests.codes.ok
            and fbs_orders_statuses_api_response.status_code == requests.codes.ok
            and sales_api_response.status_code == requests.codes.ok)


def product_list(access, page_size=50):
    """
        Получение генератора с "сырыми" данными товаров в формате JSON.
        Каждый вызов функции next() возвращает 1 объект.
            Аргументы:
                access (dict): Словарь с данными для авторизации в API.
                page_size (int): Максимальное количество карточек товаров,
                                 которые надо вывести.
            Возвращает:
                product (json): Генератор.
    """
    session = _get_session_for_content_api(
        authorization_token=access['CONTENT_API_AUTHORIZATION_TOKEN']
    )

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
            return

        products = response_data['result']['cards']
        for product in products:
            yield product


def statistics_sales_list(access, from_datetime):
    """
        Получение генератора с "сырыми" данными продаж в формате JSON.
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
        return []

    return response.json()


def fbs_orders_statuses_list(access, from_datetime, to_datetime):
    response = requests.get(
        url=urljoin(FBS_ORDERS_STATUSES_BASE_API, '/api/public/v1/supply_tasks/status'),
        params={
            'date_start': from_datetime.isoformat(),
            'date_end': to_datetime.isoformat()
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )

    if response.status_code != requests.codes.ok:
        return []

    order_statuses = []
    for order in response.json():
        last_status = order['items'][0]
        for order_status in order['items']:
            if (dateutil.parser.parse(order_status['date'])
                        > dateutil.parser.parse(last_status['date'])
                    ):
                last_status = order_status
        order_statuses.append({
            'order_id': int(order['order_id']),
            'status': last_status['status'],
        })
    return order_statuses


def fbs_order_list(access, from_datetime, to_datetime):
    """
        Получение генератора с "сырыми" данными заказов,
        сопоставленных с продажими и статусами заказов в формате JSON.
        Каждый вызов функции next() возвращает 1 объект.
            Параметры:
                access (dict): Словарь с данными для авторизации в API.
                from_datetime (datetime): Конкретная дата с которой выгружать продажи.
                to_datetime (datetime): Конкретная дата по которую выгружать заказы.
            Возвращает:
                order (json): Генератор.
    """
    response = requests.get(
        url=urljoin(FBS_ORDERS_BASE_API, '/api/v1/orders'),
        params={
            'date_start': from_datetime.isoformat(),
            'date_end': to_datetime.isoformat()
        },
        headers={'X-Auth-Token': access['ORDERS_API_TOKEN']}
    )

    if response.status_code != requests.codes.ok:
        return []

    response_data = response.json()

    order_items = []
    for order in response_data:
        for order_item in order['items']:
            order_items.append({
                'date_created': order['date_created'],
                'order_id': int(order['order_id']),
                'wb_wh_id': order['wb_wh_id'],
                'chrt_id': order_item['chrt_id'],
                'status': order_item['status'],
                'rid': int(order_item['rid']),
                'total_price': order_item['total_price'],
            })
    sales_df = pd.DataFrame.from_records(
        data=statistics_sales_list(
            access=access,
            from_datetime=from_datetime
        ),
        index='rid',
        exclude=[
            'realizationreport_id',
            'suppliercontract_code',
            'rrd_id',
            'gi_id',
            'subject_name',
            'brand_name',
            'sa_name',
            'barcode', # ?
            'doc_type_name',
            'supplier_oper_name',
            'order_dt', 'sale_dt', 'rr_dt',
            'shk_id',
            'office_name',
            'gi_box_type_name',
        ]
    )
    orders_statuses_df = pd.DataFrame.from_records(
        data=fbs_orders_statuses_list(
            access=access,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
        ),
    )

    pd.set_option('display.max_columns', None)

    order_items_df = pd.DataFrame.from_records(order_items, index='rid') \
        .merge(sales_df, on='rid', how='left') \
        .merge(orders_statuses_df, on='order_id', how='left')
    order_items_df['total_price'] = order_items_df['total_price'].apply(lambda x: x / 100)
    order_items_df['status_x'] = order_items_df['status_x'].fillna(0)
    order_items_df['status_y'] = order_items_df['status_y'].fillna(0)
    order_items_df['status'] = order_items_df \
        .apply(lambda x: '%s%s' % (int(x['status_x']), int(x['status_y'])), axis=1)
    order_items_df = order_items_df.drop(columns=[
        'status_x', 'status_y',
    ])

    order_item_financial_columns = [
        'nds',
        'cost_amount',
        'retail_price',
        'retail_amount',
        'retail_commission',
        'sale_percent',
        'commission_percent',
        'customer_reward',
        'supplier_reward',
        'retail_price_withdisc_rub',
        'for_pay',
        'for_pay_nds',
        'delivery_amount',
        'return_amount',
        'delivery_rub',
        'product_discount_for_report',
        'supplier_promo',
        'supplier_spp',
    ]
    order_item_group_columns = [
        'chrt_id',
        'wb_wh_id',
        'total_price',
        'nm_id',
        'ts_name',
        'quantity',
    ]
    order_group_columns = [
        'order_id',
        'date_created',
        'status',
    ]
    for order, order_items in order_items_df.groupby(by=order_group_columns):
        order_items = order_items.drop(columns=order_group_columns)

        order_items = order_items \
            .groupby(by=order_item_group_columns, dropna=False) \
            .agg({c: 'sum' for c in order_item_financial_columns}) \
            .reset_index()

        yield simplejson.loads(simplejson.dumps({
            'order_id': int(order[0]),
            'date_created': order[1],
            'status': order[2],
            'items': order_items.to_dict(orient='records')
        } , ignore_nan=True))
