from django.contrib import admin

from .models import ProductCard, Store, ProductCardImage


@admin.register(ProductCard)
class ProductCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'wb_product_id', 'price', 'created_at', 'updated_at')
    list_display_links = ('sku', )
    search_fields = ('sku', )


@admin.register(Store)
class ProductCardAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductCardImage)
class ProductCardAdmin(admin.ModelAdmin):
    pass