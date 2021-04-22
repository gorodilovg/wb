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


def _make_response_to_card_list_endpoint(session, offset=0, limit=10):
    """Получение "сырых" данных с API-эндпоинта,
       возвращающего список карточек товаров.
    """
    response = session.post(
        url=urljoin(BASE_API, "/card/list"),
        json=_get_initial_data(offset=offset, limit=limit)
    )
    return response.json()


def get_products_list(session, offset, limit):
    """Получение генератора с "сырыми" данными в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.

            Параметры:
                offset (int): Количество карточек,
                              которые с самого начала списка нужно пропустить.
                limit (int): Максимальное количество карточек, которые надо вывести.

            Возвращает:
                product (json): Генератор.
    """
    response_data = _make_response_to_card_list_endpoint(
        session=session, offset=offset, limit=limit
    )

    if "result" not in response_data:
        return

    for product in response_data["result"]["cards"]:
        yield product