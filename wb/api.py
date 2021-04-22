from urllib.parse import urljoin
from uuid import uuid4

import requests

SUPPLIER_ID = "1dcb7ee0-c876-5744-b19e-aa11e159abf0"
AUTHORIZATION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NJRCI6ImNkMTQ1MTM0LTNkMTktNDlmZi04NjFhLWEwZjBjNjgwYzUwZCJ9.CEH2cD8ctIjd0zPndLKBxrd_mWV7l4w5hyWusJKM4xg"


def product_list(session, offset, limit):
    """Получение карточек товаров.

            Параметры:
                offset (int): Количество карточек, которые с самого начала списка нужно пропустить.
                limit (int): Максимальное количество карточек, которые надо вывести.

            Возвращает:
                item (json): TODO
    """
    initial_data = {
        "jsonrpc": "2.0",
        "id": str(uuid4()),
        "params": {
            "supplierID": f"{SUPPLIER_ID}",
            "query": {
                "limit": limit,
                "offset": offset
            }
        }
    }

    response_data = session.post(
        url=urljoin("https://suppliers-api.wildberries.ru", "/card/list"),
        json=initial_data
    ).json()

    if "result" not in response_data:
        return

    _cards = response_data.result.cards

    for card in _cards:


s = requests.Session()
s.headers.update({
    "Authorization": AUTHORIZATION_TOKEN,
    "Content-Type": "application/json",
})

if __name__ == '__main__':
    pass
