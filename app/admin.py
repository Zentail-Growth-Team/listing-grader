from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe
from .models import (
    Seller,
    Submission,
    AnalysisResult,
    ProductAnalysisResult
)
from .tasks import process_submission


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('email', 'seller_id')
    search_fields = ['email', 'seller_id', 'seller_name']


@admin.register(Submission)
class Submission(admin.ModelAdmin):
    list_display = ('seller', 'timestamp', 'status', 'ip_address', 'source', 'resubmit')
    search_fields = ['seller__email', 'seller__seller_id', 'seller__seller_name']

    def resubmit(self, obj):
        return mark_safe(f"<a class='button' href={reverse('resubmit', args=[obj.pk])}>Resubmit</a>")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.source = obj.ADMIN
            form.fields['source'] = obj.ADMIN
        super().save_model(request, obj, form, change)
        process_submission(obj.pk)


@admin.register(AnalysisResult)
class AnalysisResult(admin.ModelAdmin):
    list_display = ('seller', 'submission', 'results_url')
    search_fields = ['seller__email', 'seller__seller_id', 'seller__seller_name']


@admin.register(ProductAnalysisResult)
class ProductAnalysisResult(admin.ModelAdmin):
    list_display = ('seller', 'submission', 'product')
    search_fields = ['seller__email', 'seller__seller_id', 'seller__seller_name']

