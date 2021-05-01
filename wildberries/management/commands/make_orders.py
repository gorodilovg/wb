import datetime

from django.core.management.base import BaseCommand

from pytz import timezone

from wildberries.consts import (
    CONTENT_API_AUTHORIZATION_TOKEN, SUPPLIER_ID,
    STATISTICS_API_KEY, ORDERS_API_TOKEN
)
from wildberries import api
from wildberries import utils
from wildberries.models import Store


ACCESS = {
    "CONTENT_API_AUTHORIZATION_TOKEN": CONTENT_API_AUTHORIZATION_TOKEN,
    "SUPPLIER_ID": SUPPLIER_ID,
    "STATISTICS_API_KEY": STATISTICS_API_KEY,
    "ORDERS_API_TOKEN": ORDERS_API_TOKEN
}
tz = timezone('UTC')


from_datetime = tz.localize(datetime.datetime(year=2021, month=4, day=1))
to_datetime = tz.localize(datetime.datetime(year=2021, month=5, day=1))

class Command(BaseCommand):

    def handle(self, *args, **options):
        store = Store.objects.get(pk=1)
        for _posting in api.fbs_order_list(ACCESS, from_datetime, to_datetime):
            order = utils.make_fbs_order(store, _posting)