import decimal
import hashlib
import json

import dateutil.parser
import numpy as np
import simplejson
from django.db import transaction
from django.utils import timezone

# from ..models import Order, OrderItem, ProductCard
from wildberries.models import Order, OrderItem, ProductCard


def get_product_price(variations):
    for variation in variations:
        for addin_object in variation['addin']:
            if addin_object['type'] == 'Розничная цена':
                return decimal.Decimal(addin_object['params'][0]['count'])


def get_product_images(addin):
    for addin_object in addin:
        if addin_object['type'] == 'Фото':
            return [image['value'] for image in addin_object['params']]


def get_product_name(addin):
    for addin_object in addin:
        if addin_object['type'] == 'Наименование':
            return addin_object['params'][0]['value'][:256]


def get_product_description(addin):
    for addin_object in addin:
        if addin_object['type'] == 'Описание':
            return addin_object['params'][0]['value']


def make_product_card(store, raw_data):
    _product_data = raw_data
    if not _product_data:
        return None

    product_card = None
    with transaction.atomic():
        now = timezone.localtime(timezone.now())
        for _nomenclature in _product_data['nomenclatures']:
            product_card_sku = '{}{}'.format(
                _product_data['supplierVendorCode'], _nomenclature['vendorCode']
            )

            try:
                product_card, _ = store.product_cards.get_or_create(
                    wildberries_character_id=_nomenclature['variations'][0]['chrtId'],
                    defaults={
                        'created_at': dateutil.parser.parse(_product_data['createdAt']),
                        'updated_at': now,
                        'sku': product_card_sku,
                        'wildberries_product_id': _product_data['id'],
                        'wildberries_character_id': _nomenclature['variations'][0]['chrtId']
                    }
                )
            except ProductCard.MultipleObjectsReturned:
                # В случае обнаружения дубликатов ProductCard
                # удаляем их

                product_card_qs = store.product_cards \
                    .filter(sku=product_card_sku) \
                    .order_by('id')
                product_card = product_card_qs.first()

                # Удаляем дубликаты
                product_card_qs \
                    .exclude(id=product_card.id) \
                    .delete()

            # проверка карточки товара на изменения
            product_data_checksum = hashlib.md5(
                json.dumps(_product_data, sort_keys=True).encode('utf-8')).hexdigest()
            if product_card.product_data_checksum == product_data_checksum:
                ProductCard.objects \
                    .filter(id=product_card.id) \
                    .update(updated_at=now)
                return product_card

            product_card.updated_at = now
            product_card.name = get_product_name(_product_data['addin'])
            product_card.price = get_product_price(_nomenclature['variations'])
            product_card.description = get_product_description(_product_data['addin'])
            product_card.status = ProductCard.PROCESSED
            product_card.raw_data = _product_data
            product_card.sku = product_card_sku

            product_card.wildberries_fbs_sku = _nomenclature['nmId']

            # добавление изображений к карточке товара
            image_ids = []
            for _image in get_product_images(_nomenclature['addin']):
                image, _ = product_card.images.get_or_create(
                    remote_file_url=_image
                )
                image_ids.append(image.id)

            # Удаляем неиспользуемые изображения
            product_card.images \
                .exclude(id__in=image_ids) \
                .delete()

            # Устанавливаем основное изображение
            # карточки товара
            if image_ids:
                product_card.image_id = image_ids[0]
            else:
                product_card.image_id = None

            product_card.save()
    return product_card


def make_fbs_order(store, raw_data, rebuild=False):
    _order = raw_data
    if not _order:
        return None

    now = timezone.localtime(timezone.now())

    order = None
    with transaction.atomic():
        try:
            order, _ = store.orders.get_or_create(
                number=_order['order_id'],
                defaults={
                    'created_at': timezone.localtime(dateutil.parser.parse(_order['date_created'])),
                    'updated_at': now,
                    'in_process_at': timezone.localtime(dateutil.parser.parse(_order['date_created'])),
                    'number': _order['order_id'],
                    'posting_type': Order.WILDBERRIES_FBS,
                    # 'status': Order.parse_status(_order['status'], 'wildberries'),
                }
            )
        except Order.MultipleObjectsReturned:
            # В случае обнаружения дубликатов Order
            # удаляем их

            order_qs = store.orders \
                .filter(number=_order['order_id']) \
                .order_by('id')
            order = order_qs.first()

            # Удаляем дубликаты
            order_qs \
                .exclude(id=order.id) \
                .delete()

        order_data_checksum = hashlib.md5(json.dumps(_order, sort_keys=True).encode('utf-8')).hexdigest()
        if not rebuild and order.order_data_checksum == order_data_checksum:
            return order

        for _product_data in _order['items']:
            if np.isnan(_product_data['nm_id']):
                continue

            order_item_changed = False

            try:
                order_item, _ = order.items.get_or_create(
                    wildberries_fbs_sku=_product_data['nm_id'],
                    defaults={
                        'wildberries_character_id': _product_data['chrt_id']
                    }
                )
            except OrderItem.MultipleObjectsReturned:
                # В случае обнаружения дубликатов OrderItem
                # удаляем их

                order_item_qs = order.items \
                    .filter(wildberries_fbs_sku=_product_data['nm_id']) \
                    .order_by('id')
                order_item = order_item_qs.first()

                # Удаляем дубликаты
                order_item_qs \
                    .exclude(id=order_item.id) \
                    .delete()

            product_data_checksum = hashlib.md5(json.dumps(_product_data, sort_keys=True).encode('utf-8')).hexdigest()
            if rebuild or not order_item.product_data_checksum == product_data_checksum:
                order_item_changed = True

                order_item.raw_product_data = _product_data
                order_item.quantity = _product_data['quantity']
                order_item.price = _product_data['total_price'] / 100  # перевод копеек в рубли
                order_item.commission = _product_data['retail_commission']
                order_item.delivery_cost = _product_data['delivery_rub']

                if not order_item.product_card_id:
                    try:
                        product_card, _ = store.product_cards.get_or_create(
                            wildberries_character_id=_product_data['chrt_id'],
                            defaults={
                                'created_at': dateutil.parser.parse(_order['date_created']),
                                'updated_at': now,
                                'sku': _product_data['sa_name'],
                                'name': _product_data['subject_name'],
                                'price': _product_data['total_price'] / 100,  # перевод копеек в рубли,
                                'wildberries_fbs_sku': _product_data['nm_id'],
                                'wildberries_character_id': _product_data['chrt_id'],
                                'raw_data': _product_data
                            })
                    except ProductCard.MultipleObjectsReturned:
                        # В случае обнаружения дубликатов ProductCard
                        # удаляем их

                        product_card_qs = store.product_cards \
                            .filter(sku=_product_data['sa_name']) \
                            .order_by('id')
                        product_card = product_card_qs.first()

                        # Удаляем дубликаты
                        product_card_qs \
                            .exclude(id=product_card.id) \
                            .delete()
                    order_item.product_card = product_card

                if order_item_changed:
                    order_item.updated_at = now
                    order_item.save()

        order.updated_at = now
        order.raw_data = simplejson.loads(simplejson.dumps(_order, ignore_nan=True))
        order.save()

    return order
