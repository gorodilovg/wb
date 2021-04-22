from datetime import datetime
from urllib.parse import urljoin

import requests

from wb.consts import API_KEY


BASE_API = "https://suppliers-stats.wildberries.ru"

def _get_initial_params(from_datetime):
    """Формирование начальных параметров, для получения заказов.

        Возвращает словарь с полями:
            dateFrom (str): Конкретная дата для выгрузки заказов.
            flag (int): Будет выгружена информация обо всех заказах или продажах
                        с датой равной переданному параметру dateFrom
                        (!NB: время в дате значения не имеет).
                        При этом количество возвращенных строк данных равно количеству всех
                        заказов или продаж, сделанных в дате, переданной в параметре dateFrom.
    """
    return {
        "key": API_KEY,
        "dateFrom": from_datetime,
        "flag": 1
    }


def check_connection(session):
    """Проверка работы /api/v1/supplier/orders API-эндпоинта suppliers-stats.wildberries.ru."""
    response = session.get(
        url=urljoin(BASE_API, "/api/v1/supplier/orders"),
        params=_get_initial_params(from_datetime=datetime.now()))
    return response.status_code == requests.codes.ok


def _get_response_from_orders_list_endpoint(session, from_datetime):
    """Получение "сырых" данных с API-эндпоинта,
       возвращающего список заказов.
    """
    response = session.get(
        url=urljoin(BASE_API, "/api/v1/supplier/orders"),
        params=_get_initial_params(from_datetime=from_datetime))
    if response.status_code == requests.codes.ok:
        return response.json()


def get_orders_list(session, from_datetime, to_datetime=None):
    """Получение генератора с "сырыми" данными в формате JSON.
       Каждый вызов функции next() возвращает 1 объект.

            Параметры:
                from_datetime (datetime): Конкретная дата для выгрузки заказов.
                to_datetime (datetime): Необязательный параметр, который не нужно передавать.
                                        Сделано для обратной совместимости с Ozon API.
            Возвращает:
                order (json): Генератор.
    """
    response_data = _get_response_from_orders_list_endpoint(
        session=session, from_datetime=from_datetime.isoformat()
    )

    for order in response_data:
        yield order
    else:
        return