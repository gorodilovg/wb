from django.contrib import admin

from .models import ProductCard, Store, ProductCardImage


@admin.register(ProductCard)
class ProductCardAdmin(admin.ModelAdmin):
    pass


@admin.register(Store)
class ProductCardAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductCardImage)
class ProductCardAdmin(admin.ModelAdmin):
    pass