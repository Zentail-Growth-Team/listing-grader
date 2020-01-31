from django.db import models
from pytz import timezone


class Seller(models.Model):
    email = models.EmailField(db_index=True)
    seller_id = models.CharField(max_length=100, db_index=True)
    seller_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.seller_name}-{self.seller_id}'

    class Meta:
        unique_together = ['email', 'seller_id']


class Submission(models.Model):
    SUBMITTED = 'submitted'
    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILURE = 'failure'
    STATUS_CHOICES = [
        (SUBMITTED, 'Submitted'),
        (PROCESSING, 'Processing'),
        (SUCCESS, 'Success'),
        (FAILURE, 'Failure')
    ]
    timestamp = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    limit_results = models.IntegerField(default=20, help_text="Use '0' for no limit")
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default=SUBMITTED)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        eastern = timezone('US/Eastern')
        return f"{self.seller.seller_id} - {(self.timestamp.astimezone(eastern)).strftime('%b %d, %Y,  %I:%M %p')}"


class AnalysisResult(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    results_url = models.URLField(blank=True, null=True)
    copy_score = models.FloatField()
    media_score = models.FloatField()
    feedback_score = models.FloatField()
    extra_content_score = models.FloatField()
    seller_image_url = models.URLField(blank=True, null=True)
    webflow_cms_id = models.CharField(max_length=255, blank=True, null=True)


class ProductAnalysisResult(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    product = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    title_score = models.IntegerField()
    title_character_count = models.IntegerField()
    title_contains_promo_phrase = models.BooleanField()
    title_contains_single_quote = models.BooleanField()
    title_contains_ascii = models.BooleanField()
    title_contains_seo_adverse_chars = models.BooleanField()
    title_num_lower_case = models.IntegerField()
    title_num_all_caps = models.IntegerField()
    title_num_incorrect_caps = models.IntegerField()
    title_contains_dollar_sign = models.BooleanField()
    description_score = models.IntegerField()
    description_character_count = models.IntegerField()
    description_contains_quotes = models.BooleanField()
    description_contains_html = models.BooleanField()
    description_contains_price_condition_info = models.BooleanField()
    description_contains_shipping_info = models.BooleanField()
    description_contains_contact_info = models.BooleanField()
    description_num_lower_case_bullets = models.IntegerField()
    description_num_bullets = models.IntegerField()
    bullets_score = models.IntegerField()
    media_score = models.IntegerField()
    media_num_images = models.IntegerField()
    media_low_qual_images = models.IntegerField()
    media_high_whitespace_images = models.IntegerField()
    media_num_videos = models.IntegerField()
    ratings_reviews_score = models.IntegerField()
    rating = models.FloatField()
    num_reviews = models.IntegerField()
    feature_image_url = models.URLField(blank=True, null=True)
    extra_content_score = models.IntegerField()
