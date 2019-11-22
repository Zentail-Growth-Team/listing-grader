import requests
from background_task import background
from bs4 import BeautifulSoup
from django.conf import settings
from .analysis_utils import analyze_products, calculate_product_scores
from .models import Submission, ProductAnalysisResult, AnalysisResult
from .webflow_utils import send_to_webflow


@background()
def process_submission(submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
        seller_page = requests.get(f"https://www.amazon.com/sp?seller={submission.seller.seller_id}")
        bs = BeautifulSoup(seller_page.text)
        seller_name = bs.find('sellerName').text if bs.find('sellerName') else ''
        seller = submission.seller
        seller.seller_name = seller_name
        seller.save()
        seller_image_attrs = bs.find(id='sellerLogo').attrs if bs.find(id='sellerLogo') else {}
        seller_image_url = seller_image_attrs['src'] if 'src' in seller_image_attrs else ''
        full_product_list = []
        pagination = True
        page = 1
        while pagination:
            zinc_api_url = f"{settings.ZINC_SELLER_API_URL}?seller_id={submission.seller.seller_id}&retailer=amazon&page={page}"
            response = requests.get(url=zinc_api_url, auth=(settings.ZINC_API_TOKEN, ""))
            print(f"Request num:{page}")
            if response.status_code == 200:
                print(response.json())
                try:
                    data = response.json()
                    full_product_list += (data['results'])
                    print(f"{data['showing']}")
                    if data['showing']['end'] == data['showing']['of']:
                        pagination = False
                    if submission.limit_results != 0 and len(full_product_list) >= submission.limit_results:
                        pagination = False
                    page += 1
                except KeyError:
                    print('key error')
            else:
                # TODO: Log errors
                pass
        results = analyze_products(full_product_list)
        print('********Finished analyzing all products')
        seller_title_score_total = 0
        seller_description_score_total = 0
        seller_bullets_score_total = 0
        seller_media_score_total = 0
        seller_reviews_score_total = 0
        seller_extra_score_total = 0
        best_rated_product_image_url = ''
        best_rated_product_score = 0
        for result in results:
            print(f"Calculating scores for {result['product_id']}")
            scores = calculate_product_scores(result)
            seller_title_score_total += scores['title_score']
            seller_description_score_total += scores['description_score']
            seller_bullets_score_total += scores['bullets_score']
            seller_media_score_total += scores['media_score']
            seller_reviews_score_total += scores['ratings_and_reviews_score']
            new_product_analysis = ProductAnalysisResult(
                seller=submission.seller,
                submission=submission,
                product=result['product_id'],
                title=result['title']['title'][0:255],
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
        print('Save analysis')
        new_seller_analysis = AnalysisResult(
            seller=submission.seller,
            submission=submission,
            copy_score=seller_copy_score,
            media_score=seller_media_score_total/len(results),
            feedback_score=seller_reviews_score_total/len(results),
            extra_content_score=seller_extra_score_total/len(results),
            seller_image_url=seller_image_url,
        )
        new_seller_analysis.save()
        print('Saved')
        send_to_webflow(submission_id)

    except Submission.DoesNotExist:
        # TODO: Log errors
        pass

