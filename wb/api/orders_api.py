from urllib.parse import urljoin

import requests

from wb.consts import API_KEY


BASE_API = "https://suppliers-stats.wildberries.ru"

def _get_initial_params(from_datetime):
    """Формирование начальных параметров, для получения закозов."""
    return {
        "key": API_KEY,
        "dateFrom": from_datetime
    }


def check_connection(session):
    """Проверка работы /api/v1/supplier/orders API-эндпоинта suppliers-stats.wildberries.ru."""
    response = session.get(
        url=urljoin(BASE_API, "/api/v1/supplier/orders"),
        params=_get_initial_params())
    return response.status_code == requests.codes.ok

