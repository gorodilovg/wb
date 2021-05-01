from django.contrib import admin

from .models import ProductCard, Store, ProductCardImage, Order, OrderItem


@admin.register(ProductCard)
class ProductCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sku', 'wildberries_product_id', 'wildberries_character_id', 'price', 'created_at', 'updated_at')
    list_display_links = ('sku', )
    search_fields = ('sku', )


@admin.register(Store)
class ProductCardAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductCardImage)
class ProductCardAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'created_at', 'updated_at')
    list_display_links = ('number', )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'price', 'product_card', 'wildberries_character_id', 'updated_at')
    list_display_links = ('order',)
    search_fields = ('order__number', 'wildberries_fbs_sku',)