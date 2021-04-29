import decimal
import hashlib
import json

from django.db import models
from django.contrib.postgres.fields import JSONField


def raw_data_default():
    return {}


class IdentifierMixin(models.Model):
    identifier = models.CharField('идентификатор', max_length=256, blank=True,
                                  db_index=True, default='', editable=False)

    class Meta(object):
        abstract = True


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
    last_download_products = models.DateTimeField(null=True, blank=True)
    last_download_ozon_fbo_postings = models.DateTimeField(null=True, blank=True)
    last_download_ozon_fbs_postings = models.DateTimeField(null=True, blank=True)
    last_update_ozon_orders = models.DateTimeField(null=True, blank=True)

    disabled_reason = models.CharField('причина отключения', max_length=256,
                                       default='', blank=True, choices=DISABLED_REASON_CHOICES)

    class Meta(object):
        verbose_name = 'магазин'
        verbose_name_plural = 'магазины'
        ordering = ('-id', )


class ProductCard(IdentifierMixin):
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
    store = models.ForeignKey('Store', on_delete=models.SET_NULL,
                                related_name='product_cards', null=True)
    raw_data = JSONField(default=raw_data_default)

    @property
    def product_data_checksum(self):
        return hashlib.md5(json.dumps(self.raw_data, sort_keys=True).encode('utf-8')).hexdigest()

    def __str__(self):
        return self.sku


class Order(IdentifierMixin):
    OZON_FBO = 'ozon_fbo'
    OZON_FBS = 'ozon_fbs'

    TYPE_CHOICES = [
        (OZON_FBO, 'Ozon FBO'),
        (OZON_FBS, 'Ozon FBS'),
    ]

    AWAITING_APPROVE = 'awaiting_approve'
    AWAITING_PACKAGING = 'awaiting_packaging'
    AWAITING_DELIVER = 'awaiting_deliver'
    DELIVERING = 'delivering'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    NOT_ACCEPTED = 'not_accepted'

    STATUS_CHOICES = [
        (AWAITING_APPROVE, 'Ожидает подтверждения'),
        (AWAITING_PACKAGING, 'Ожидает упаковки'),
        (AWAITING_DELIVER, 'Ожидает отгрузки'),
        (DELIVERING, 'Доставляется'),
        (DELIVERED, 'Доставлено'),
        (CANCELLED, 'Аннулировано'),
        (NOT_ACCEPTED, 'Не принят в сортировочном центре'),
    ]

    created_at = models.DateTimeField(
        verbose_name='дата и время',
        null=True)
    updated_at = models.DateTimeField(
        verbose_name='дата и время обновления',
        null=True)
    in_process_at = models.DateTimeField(
        verbose_name='принят в обработку',
        null=True)
    number = models.CharField(
        verbose_name='номер',
        max_length=64,
        default='',
        db_index=True)
    posting_type = models.CharField(
        verbose_name='тип отправления',
        max_length=32,
        default='',
        choices=TYPE_CHOICES)
    posting_number = models.CharField(
        verbose_name='номер отправления',
        max_length=64,
        default='',
        db_index=True)
    status = models.CharField(
        verbose_name='статус',
        max_length=32,
        default='',
        choices=STATUS_CHOICES)
    fixed_expenses_of_store = models.DecimalField(
        'фиксированные расходы магазина',
        max_digits=10, decimal_places=2,
        default=decimal.Decimal(0))
    other_expenses_of_store = models.DecimalField(
        'прочие расходы магазина',
        max_digits=10, decimal_places=2,
        default=decimal.Decimal(0))
    store = models.ForeignKey('Store', on_delete=models.SET_NULL,
                              related_name='orders', null=True)


class OrderItem(models.Model):
    updated_at = models.DateTimeField(
        verbose_name='дата и время обновления',
        null=True)
    quantity = models.IntegerField('количество', default=0)
    price = models.DecimalField('цена', max_digits=10, decimal_places=2,
                                default=decimal.Decimal(0))
    purchase_price = models.DecimalField('закупочная цена', max_digits=12,
                                         decimal_places=4, blank=True, null=True,
                                         default=None)
    product_total_cost = models.DecimalField('себестоимость товара', max_digits=12,
                                             decimal_places=4, blank=True, null=True,
                                             default=None)
    product_reject_rate = models.DecimalField('процент брака', max_digits=5,
                                             decimal_places=2, blank=True, null=True,
                                             default=None)
    product_return_rate = models.DecimalField('процент возврата товара', max_digits=5,
                                             decimal_places=2, blank=True, null=True,
                                             default=None)
    packing_cost = models.DecimalField('стоимость упаковки', max_digits=10,
                                       decimal_places=2, blank=True, null=True,
                                       default=None)
    delivery_cost = models.DecimalField('стоимость доставки', max_digits=10,
                                        decimal_places=2, blank=True, null=True,
                                        default=None)
    return_cost = models.DecimalField('стоимость возврата', max_digits=10,
                                      decimal_places=2, blank=True, null=True,
                                      default=None)
    commission = models.DecimalField('комиссия', max_digits=10, decimal_places=2,
                                     blank=True, null=True,
                                     default=None)
    product_card = models.ForeignKey('ProductCard', on_delete=models.SET_NULL,
                                     related_name='order_items', null=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE,
                              related_name='items', null=True)

    ozon_fbs_sku = models.CharField(max_length=128, default='', blank=True)
    ozon_fbo_sku = models.CharField(max_length=128, default='', blank=True)

    raw_product_data = JSONField(default=raw_data_default)
    raw_financial_data = JSONField(default=raw_data_default)