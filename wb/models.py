import decimal

from django.db import models
from django.contrib.postgres.fields import JSONField


def raw_data_default():
    return {}


class IdentifierMixin(models.Model):
    identifier = models.CharField('идентификатор', max_length=256, blank=True,
                                  db_index=True, default='', editable=False)

    class Meta(object):
        abstract = True

    # def save(self, *args, **kwargs):
    #     if not self.identifier:
    #         reset_identifier(self)
    #
    #     return super().save(*args, **kwargs)
    #
    # def reset_identifier(self):
    #     if self.id is None:
    #         return
    #
    #     identifier = reset_identifier(self)
    #     self.__class__.objects \
    #         .filter(id=self.id) \
    #         .update(identifier=identifier)


class ProductCardImage(models.Model):
    remote_file_url = models.CharField(max_length=256, default='', blank=True)
    product_card = models.ForeignKey('wb.ProductCard', on_delete=models.CASCADE,
                                     related_name='images',
                                     null=True)

    class Meta(object):
        indexes = [
            models.Index(fields=['remote_file_url', ]),
        ]

    def _get_file(self):
        return self.remote_file_url

    file = property(_get_file)


class Store(IdentifierMixin):
    CONNECT_FAILED_OZON_API = 'connect_failed_ozon_api'

    DISABLED_REASON_CHOICES = [
        (CONNECT_FAILED_OZON_API, 'Не удалось подключится к Ozon Seller API. Проверьте Client ID и API Key.'),
    ]

    created_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    name = models.CharField('name', max_length=256, default='')
    opening_date = models.DateField('дата открытия', null=True)
    # users = models.ManyToManyField('account.User', related_name='stores',
    #                                through='core.StoreUser')
    # company = models.ForeignKey('core.Company', related_name='stores',
    #                             on_delete=models.PROTECT, null=True)

    last_download_products = models.DateTimeField(null=True, blank=True)
    last_download_ozon_fbo_postings = models.DateTimeField(null=True, blank=True)
    last_download_ozon_fbs_postings = models.DateTimeField(null=True, blank=True)
    last_update_ozon_orders = models.DateTimeField(null=True, blank=True)

    disabled_reason = models.CharField('причина отключения', max_length=256,
                                       default='', blank=True, choices=DISABLED_REASON_CHOICES)

    # objects = StoreManager()

    class Meta(object):
        verbose_name = 'магазин'
        verbose_name_plural = 'магазины'
        ordering = ('-id', )


class ProductCard(IdentifierMixin):
    # SEARCH_VECTOR = (
    #     SearchVector('sku', weight='A') + SearchVector('name', weight='B')
    # )

    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    sku = models.CharField('артикул', max_length=128, blank=True, default='',
                           db_index=True)
    name = models.CharField('имя', max_length=256, default='')
    price = models.DecimalField('цена', max_digits=10, decimal_places=2, default=decimal.Decimal(0))
    description = models.TextField('описание', default='', blank=True)
    wb_product_id = models.PositiveIntegerField(default=0, blank=True)
    wb_category_id = models.PositiveIntegerField(default=0, blank=True)
    image = models.ForeignKey('ProductCardImage', on_delete=models.SET_NULL,
                              related_name='+', blank=True, null=True)
    # products = models.ManyToManyField(
    #     to='core.Product',
    #     related_name='product_cards',
    #     through='core.ProductCardRelatedProduct',
    #     through_fields=('product_card', 'product'),
    # )
    store = models.ForeignKey('Store', on_delete=models.SET_NULL,
                                related_name='product_cards', null=True)

    # search_vector = SearchVectorField(null=True, editable=False)

    raw_data = JSONField(default=raw_data_default)

    # objects = ProductCardManager()

    def __str__(self):
        return self.sku