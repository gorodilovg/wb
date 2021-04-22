import math
from uuid import uuid4
from urllib.parse import urljoin

import requests

from wb.consts import SUPPLIER_ID


BASE_API = "https://suppliers-api.wildberries.ru"

def _get_initial_data(offset, limit):
    """Формирование начальных данных, для получения карточек товаров."""
    return {
        "jsonrpc": "2.0",
        "id": str(uuid4()),
        "params": {
            "supplierID": SUPPLIER_ID,
            "query": {
                "offset": offset,
                "limit": limit
            }
        }
    }


def check_connection(session):
    """Проверка работы /card/list/ API-эндпоинта suppliers-api.wildberries.ru."""
    response = session.post(
        url=urljoin(BASE_API, "/card/list"),
        json=_get_initial_data(offset=0, limit=1))
    return response.status_code == requests.codes.ok


def _get_response_from_card_list_endpoint(session, offset, limit):
    """Получение "сырых" данных с API-эндпоинта,
       возвращающего список карточек товаров.

       Параметры:
                offset (int): Количество карточек,
                              которые с самого начала списка нужно пропустить.
                limit (int): Максимальное количество карточек, которые надо вывести.
    """
    response = session.post(
        url=urljoin(BASE_API, "/card/list"),
        json=_get_initial_data(offset=offset, limit=limit)
    )
    return response.json()


def get_products_list(session):
    """Получение генератора с "сырыми" данными в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.

            Возвращает:
                product (json): Генератор.
    """
    _LIMIT = 10  # Максимальное количество карточек, которые надо вывести.

    response_data = _get_response_from_card_list_endpoint(
        session=session, offset=0, limit=1)

    if "result" not in response_data:
        return

    _TOTAL_PRODUCTS = response_data["result"]["cursor"]["total"]

    for _products_list, idx in enumerate(range(0, math.ceil(_TOTAL_PRODUCTS / _LIMIT) + 1)):

        response_data = _get_response_from_card_list_endpoint(
            session=session, offset=idx*_LIMIT, limit=_LIMIT)

        if "result" not in response_data:
            continue

        products = response_data["result"]["cards"]
        for product in products:
            yield product