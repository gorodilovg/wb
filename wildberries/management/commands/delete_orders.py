from django.core.management.base import BaseCommand


from wildberries.models import Order


class Command(BaseCommand):

    def handle(self, *args, **options):
        for product in Order.objects.all():
            product.delete()