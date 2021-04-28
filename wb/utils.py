import decimal
import hashlib
import json

import pprint

import dateutil.parser
from django.db import models, transaction
from django.utils import timezone

from wb.models import ProductCard


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
        product_images = []
        if _product_data['nomenclatures']:
            for nomenclature in _product_data['nomenclatures']:
                merged_sku = f'{_product_data["supplierVendorCode"]}/{nomenclature["vendorCode"]}'
                product_images = get_product_images(nomenclature['addin'])

                try:
                    product_card, _ = store.product_cards.get_or_create(
                        sku=merged_sku,
                        defaults={
                            'wb_product_id': nomenclature['nmId'],
                            'price': get_product_price(nomenclature['variations']),
                            'name': get_product_name(_product_data['addin']),
                            'description': get_product_description(_product_data['addin']),
                            'created_at': _product_data['createdAt'],
                            'updated_at': _product_data['updatedAt'],
                            'raw_data': _product_data
                        }
                    )
                except ProductCard.MultipleObjectsReturned:
                    # В случае обнаружения дубликатов ProductCard
                    # удаляем их

                    product_card_qs = store.product_cards \
                        .filter(sku=merged_sku) \
                        .order_by('id')
                    product_card = product_card_qs.first()

                    # Удаляем дубликаты
                    product_card_qs \
                        .exclude(id=product_card.id) \
                        .delete()

        else:
            # TODO TODO TODO
            pass

        # product_data_checksum = hashlib.md5(json.dumps(_product_data, sort_keys=True).encode('utf-8')).hexdigest()
        # if product_card.product_data_checksum == product_data_checksum:
        #     ProductCard.objects \
        #         .filter(id=product_card.id) \
        #         .update(updated_at=now)
        #
        #     return product_card

        # добавление изображений к товару
        image_ids = []
        for _image in product_images:
            image, _ = product_card.images.get_or_create(
                remote_file_url=_image
            )
            image_ids.append(image.id)

        # Удаляем неиспользуемые изображения
        product_card.images \
            .exclude(id__in=image_ids) \
            .delete()

        # Устанавливаем основное изображение карточки товара
        if image_ids:
            product_card.image_id = image_ids[0]
        else:
            product_card.image_id = None

        product_card.save()

    return product_card