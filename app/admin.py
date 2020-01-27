from django.contrib import admin
from .models import (
    Seller,
    Submission,
    AnalysisResult,
    ProductAnalysisResult
)


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('email', 'seller_id')


@admin.register(Submission)
class Submission(admin.ModelAdmin):
    list_display = ('seller', 'timestamp', 'status', 'ip_address')


@admin.register(AnalysisResult)
class AnalysisResult(admin.ModelAdmin):
    list_display = ('seller', 'submission', 'results_url')


@admin.register(ProductAnalysisResult)
class ProductAnalysisResult(admin.ModelAdmin):
    list_display = ('seller', 'submission', 'product')
