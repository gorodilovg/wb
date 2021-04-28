import datetime

from django.core.management.base import BaseCommand, CommandError

from pytz import timezone

from wb.consts import (
    CONTENT_API_AUTHORIZATION_TOKEN, SUPPLIER_ID,
    STATISTICS_API_KEY, ORDERS_API_TOKEN
)
from wb import api
from wb import utils
from wb.models import Store


ACCESS = {
    "CONTENT_API_AUTHORIZATION_TOKEN": CONTENT_API_AUTHORIZATION_TOKEN,
    "SUPPLIER_ID": SUPPLIER_ID,
    "STATISTICS_API_KEY": STATISTICS_API_KEY,
    "ORDERS_API_TOKEN": ORDERS_API_TOKEN
}
tz = timezone('UTC')
from_datetime = tz.localize(datetime.datetime(year=2021, month=4, day=10))
to_datetime = tz.localize(datetime.datetime(year=2021, month=4, day=12))


class Command(BaseCommand):

    def handle(self, *args, **options):
        store = Store.objects.get(pk=1)
        for _posting in list(
            filter(lambda product: product['id'] == '59942c59-609b-5c92-b644-771792e76ded',
                   api.product_list(ACCESS))):
            product_card = utils.make_product_card(store, _posting)