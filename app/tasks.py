import logging
import requests
from background_task import background
from bs4 import BeautifulSoup
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .analysis_utils import analyze_products, calculate_product_scores
from .models import Submission, ProductAnalysisResult, AnalysisResult
from .webflow_utils import send_to_webflow
from .zapier_utils import send_to_zapier

logger = logging.getLogger(__name__)

RESULTS_BASE_URL = "https://www.zentail.com/amazon-listing-checker-results/"


@background()
def process_submission(submission_id):
    with transaction.atomic():
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.status = submission.PROCESSING
            submission.save()
            zinc_seller_name_url = f"{settings.ZINC_SELLER_NAME_API}{submission.seller.seller_id}?max_age=90&timeout=90"
            response = requests.get(url=zinc_seller_name_url, auth=(settings.ZINC_API_TOKEN, ""))
            if response.status_code == 200:
                try:
                    seller_name = response.json()['value']['results']['seller_name']
                except Exception as e:
                    logger.error("Problem getting seller name")
                    submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Invalid name data from Zinc\n"
                    submission.save()
                    seller_name = ""
            else:
                submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Zinc seller name call failure\n"
                submission.save()
                seller_name = ""
            seller = submission.seller
            seller.seller_name = seller_name
            seller.save()
            seller_image_url = ''
            full_product_list = []
            pagination = True
            page = 1
            while pagination:
                zinc_api_url = f"{settings.ZINC_SELLER_API_URL}?seller_id={submission.seller.seller_id}&retailer=amazon&page={page}&max_age=300"
                response = requests.get(url=zinc_api_url, auth=(settings.ZINC_API_TOKEN, ""))
                logger.info(f"Request num:{page}")
                if response.status_code == 200:
                    logger.info(response.json())
                    try:
                        data = response.json()
                        if data['results']:
                            full_product_list += (data['results'])
                            logger.info(f"{data['showing']}")
                            if data['showing']['end'] == data['showing']['of']:
                                pagination = False
                            if submission.limit_results != 0 and len(full_product_list) >= submission.limit_results:
                                pagination = False
                            page += 1
                        else:
                            pagination = False
                    except Exception as e:
                        pagination = False
                        logger.error(f'{e}')
                        submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Invalid seller data from Zinc\n"
                        submission.save()
                        send_to_zapier(submission.seller.email,
                                       submission.seller.seller_id,
                                       "fail",
                                       submission.seller.seller_name,
                                       "fail")
                else:
                    pagination = False
                    logger.error(response.content)
                    submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Zinc seller data call failure\n"
                    submission.save()
                    send_to_zapier(submission.seller.email,
                                   submission.seller.seller_id,
                                   "fail",
                                   submission.seller.seller_name,
                                   "fail")
            if full_product_list:
                results = analyze_products(full_product_list)
                logger.info('********Finished analyzing all products')
                seller_title_score_total = 0
                seller_description_score_total = 0
                seller_bullets_score_total = 0
                seller_media_score_total = 0
                seller_reviews_score_total = 0
                seller_extra_score_total = 0
                best_rated_product_image_url = ''
                best_rated_product_score = 0
                for result in results:
                    logger.info(f"Calculating scores for {result['product_id']}")
                    scores = calculate_product_scores(result)
                    seller_title_score_total += scores['title_score']
                    seller_description_score_total += scores['description_score']
                    seller_bullets_score_total += scores['bullets_score']
                    seller_media_score_total += scores['media_score']
                    seller_reviews_score_total += scores['ratings_and_reviews_score']
                    seller_extra_score_total += result['extra_content']
                    updated_title = result['title']['title'].replace('"', '[replace-quote]')
                    updated_title = updated_title.replace("'", '[replace-single]')
                    new_product_analysis = ProductAnalysisResult(
                        seller=submission.seller,
                        submission=submission,
                        product=result['product_id'],
                        title=updated_title[0:255],
                        title_score=scores['title_score'],
                        title_character_count=result['title']['num_chars'],
                        title_contains_promo_phrase=result['title']['contains_promo_phrase'],
                        title_contains_single_quote=result['title']['contains_single_quote'],
                        title_contains_ascii=result['title']['contains_ascii'],
                        title_contains_seo_adverse_chars=result['title']['contains_seo_adverse_chars'],
                        title_num_lower_case=result['title']['num_lower_case'],
                        title_num_all_caps=result['title']['num_all_caps'],
                        title_num_incorrect_caps=result['title']['num_incorrect_caps'],
                        title_contains_dollar_sign=result['title']['contains_dollar_sign'],
                        description_score=scores['description_score'],
                        description_character_count=result['description']['char_count'],
                        description_contains_quotes=result['description']['contains_quotes'],
                        description_contains_html=result['description']['contains_html'],
                        description_contains_price_condition_info=result['description']['contains_price_condition_info'],
                        description_contains_shipping_info=result['description']['contains_shipping_info'],
                        description_contains_contact_info=result['description']['contains_contact_info'],
                        description_num_lower_case_bullets=result['bullets']['num_lower_case_bullets'],
                        description_num_bullets=result['bullets']['num_bullets'],
                        bullets_score=scores['bullets_score'],
                        media_score=scores['media_score'],
                        media_num_images=result['media']['num_images'],
                        media_low_qual_images=result['media']['low_qual_images'],
                        media_high_whitespace_images=result['media']['high_whitespace_images'],
                        media_num_videos=result['media']['num_videos'],
                        ratings_reviews_score=scores['ratings_and_reviews_score'],
                        rating=result['ratings_and_reviews']['rating'],
                        num_reviews=result['ratings_and_reviews']['review_count'],
                        feature_image_url=result['media']['feature_image_url'],
                        extra_content_score=result['extra_content']
                    )
                    if result['ratings_and_reviews']['rating'] > best_rated_product_score:
                        if result['media']['feature_image_url']:
                            best_rated_product_score = result['ratings_and_reviews']['rating']
                            best_rated_product_image_url = result['media']['feature_image_url']
                    new_product_analysis.save()
                seller_copy_score = (((seller_title_score_total/len(results))*.425) +
                                     ((seller_description_score_total/len(results))*.425) +
                                     ((seller_bullets_score_total/len(results))*.15))
                if seller_image_url == '':
                    seller_image_url = best_rated_product_image_url
                logger.info('Save analysis')
                new_seller_analysis = AnalysisResult(
                    seller=submission.seller,
                    submission=submission,
                    copy_score=seller_copy_score,
                    media_score=seller_media_score_total/len(results),
                    feedback_score=seller_reviews_score_total/len(results),
                    extra_content_score=seller_extra_score_total/len(results),
                    seller_image_url=seller_image_url,
                    results_url=f"{RESULTS_BASE_URL}{submission.seller.seller_id}",
                )
                new_seller_analysis.save()
                logger.info('Saved')
                submission.status = submission.SUCCESS
                submission.save()
                send_to_webflow(submission_id)
                send_to_zapier(submission.seller.email,
                               submission.seller.seller_id,
                               f"{RESULTS_BASE_URL}{submission.seller.seller_id}",
                               submission.seller.seller_name,
                               "success")
            else:
                submission.status = submission.FAILURE
                submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Empty product list\n"
                submission.save()
                send_to_zapier(submission.seller.email,
                               submission.seller.seller_id,
                               "fail",
                               submission.seller.seller_name,
                               "fail")
        except Submission.DoesNotExist:
            logger.error(f"{submission_id} does not exist")
        except Exception as e:
            logger.error(f"{submission_id} could not be processed properly. Exception: {e}")
            try:
                submission.status = submission.FAILURE
                submission.notes += f"{timezone.now().strftime('%b %d, %Y,  %I:%M %p')} - Exception (check log)\n"
                submission.save()
                send_to_zapier(submission.seller.email,
                               submission.seller.seller_id,
                               "fail",
                               submission.seller.seller_name,
                               "fail")
            except Exception as e:
                logger.error(f"Couldn't send to Zapier: {e}")

