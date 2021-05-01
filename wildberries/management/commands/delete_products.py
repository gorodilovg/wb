from django.core.management.base import BaseCommand


from wildberries.models import ProductCard


class Command(BaseCommand):

    def handle(self, *args, **options):
        for product in ProductCard.objects.all():
            product.delete()