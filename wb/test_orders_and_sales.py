import datetime
from urllib.parse import urljoin

import requests
import dateutil.parser

from wb.consts import AUTHORIZATION_TOKEN, SUPPLIER_ID, API_KEY
from wb.api import order_list


ACCESS = {
    "AUTHORIZATION_TOKEN": AUTHORIZATION_TOKEN,
    "SUPPLIER_ID": SUPPLIER_ID,
    "API_KEY": API_KEY
}
STATISTICS_BASE_API = 'https://suppliers-stats.wildberries.ru'

from_datetime = datetime.datetime(year=2021, month=4, day=1)
to_datetime = datetime.datetime(year=2021, month=4, day=23)

def get_sales_list(_from_datetime, _to_datetime):
    response = requests.get(
        url=urljoin(STATISTICS_BASE_API, '/api/v1/supplier/sales'),
        params={
            'key': ACCESS['API_KEY'],
            'dateFrom': from_datetime.isoformat()
        }
    )

    response_data = response.json()

    for sale in response_data:
        sale_date = dateutil.parser.parse(sale['date'])
        if from_datetime <= sale_date <= to_datetime:
            yield sale
    else:
        yield from ()



# orders = list(order_list(access=ACCESS, from_datetime=from_datetime, to_datetime=to_datetime))
# sales = list(get_sales_list(_from_datetime=from_datetime, _to_datetime=to_datetime))

print()