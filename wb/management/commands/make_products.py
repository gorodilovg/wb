from django.core.management.base import BaseCommand

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

class Command(BaseCommand):

    def handle(self, *args, **options):
        store = Store.objects.get(pk=1)
        for _posting in api.product_list(ACCESS):
            product_card = utils.make_product_card(store, _posting)