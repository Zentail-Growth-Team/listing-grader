import re
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def contains_phone_num(string):
    regexp = re.compile(r'[2-9]\d{2}-\d{3}-\d{4}$')
    if regexp.search(string):
        return True
    else:
        return False


def get_image_stats(url):
    try:
        data = requests.get(url).content
        im = Image.open(BytesIO(data))
        width, height = im.size
        # get whitespace percentage
        px = im.load()
        ws_ctr = 0
        ws_threshold = 750  # pure white is 765

        x = 0
        colored = 0
        x_start = 0
        x_end = 0

        # get the left most columns of ws
        while x < width and colored == 0:
            y = 0
            while y < height and colored == 0:
                if px[x, y][0] + px[x, y][1] + px[x, y][2] < ws_threshold:
                    colored = 1
                y += 1
            if colored == 0:
                ws_ctr += height
            else:
                x_start = x
            x += 1

        # reset vars
        x = width - 1
        colored = 0

        # get right most columns whitespace
        while x >= x_start and colored == 0:
            y = 0
            while y < height and colored == 0:
                if px[x, y][0] + px[x, y][1] + px[x, y][2] < ws_threshold:
                    colored = 1
                y += 1
            if colored == 0:
                ws_ctr += height
            else:
                x_end = x
            x -= 1

        # reset vars
        y = 0
        colored = 0

        # get the bottom rows ws
        while y < height and colored == 0:
            x = x_start
            while x < x_end and colored == 0:
                if px[x, y][0] + px[x, y][1] + px[x, y][2] < ws_threshold:
                    colored = 1
                x += 1
            if colored == 0:
                ws_ctr += x_end - x_start
            y += 1

        # reset vars
        y = height - 1
        colored = 0

        # get the top rows ws
        while y >= 0 and colored == 0:
            x = x_start
            while x < x_end and colored == 0:
                if px[x, y][0] + px[x, y][1] + px[x, y][2] < ws_threshold:
                    colored = 1
                x += 1
            if colored == 0:
                ws_ctr += x_end - x_start
            y -= 1
    except TypeError:
        logging.error(f"Problem processing image: {url}")
        return None, None, None
    return width, height, ws_ctr / (height * width)


def analyze_products(products_list):
    results = []
    for product in products_list:
        print(f"****Analyzing product:{product['product_id']}")
        try:
            title = product['title']
            product_id = product['product_id']
        except KeyError:
            continue
        print("Getting product data")
        response = requests.get(url=f"{settings.ZINC_PRODUCT_API_URL}{product_id}?retailer=amazon&max_age=300",
                                auth=(settings.ZINC_API_TOKEN, ""))
        if response.status_code == 200:
            product_data = response.json()
            print("Product data received")
            print(product_data)
            try:
                description = product_data['product_description'] if 'product_description' in product_data else ''
                feature_bullets = product_data['feature_bullets'] if 'feature_bullets' in product_data else []
                images = product_data['images'] if 'images' in product_data else []
                videos = product_data['videos'] if 'videos' in product_data else []
                print("Analyze titles")
                title_results = analyze_title(title)
                print("Analyze descriptions")
                description_results = analyze_description(description)
                print("Analyze bullets")
                bullets_results = analyze_bullets(feature_bullets)
                print("Analyze media")
                media_results = analyze_media(images, videos)
                print("Analyze extra content")
                if 'aplus_html' in product_data and product_data['aplus_html'] is not None:
                    extra_content_results = 100
                elif 'ebc_html' in product_data and product_data['ebc_html'] is not None:
                    extra_content_results = 100
                else:
                    extra_content_results = 0
                results.append({
                    "product_id": product_id,
                    "title": title_results,
                    "description": description_results,
                    "bullets": bullets_results,
                    "media": media_results,
                    "ratings_and_reviews": {
                        "rating": product_data['stars'] if product_data['stars'] else 0,
                        "review_count": product_data['review_count'] if product_data['review_count'] else 0,
                    },
                    "extra_content": extra_content_results
                })
            except KeyError:
                print('Key Error with data')
                print(product_data)
                continue
        else:
            print(f"Problem with product:{product_id}")

    return results


def analyze_title(title):
    # Character counts
    num_chars = len(title)
    num_chars_gte_sixty = num_chars >= 60

    # Checking for promo phrases appearing in full title
    promo_phrases = ['Bargain', 'Free Shipping', 'Discount', 'Promotion', 'Promo', 'Hot Deal',
                     'Great Deal', 'Hot item', 'Best Price', 'Best Seller', 'Better', 'Trending', 'Trendy']
    if any(phrase in title.lower() for phrase in promo_phrases):
        contains_promo_phrase = True
    else:
        contains_promo_phrase = False

    # Checking for single-quote/apostrophes?
    if '\'' in title:
        contains_single_quote = True
    else:
        contains_single_quote = False

    # Checking for Type 1 ASCII
    is_ascii = (lambda s: len(s) != len(s.encode()))
    if is_ascii(title):
        contains_ascii = True
    else:
        contains_ascii = False

    # Checking for SEO-adverse characters
    bad_chars = ['~', '!', '*', '$', '?', '_', '~', '{', '}', '[', ']', '#', '&lt;', '>', '|', '*', ';', '/', '^',
                 '¬', '¦', '&']
    if any(char in title for char in bad_chars):
        contains_seo_adverse_chars = True
    else:
        contains_seo_adverse_chars = False

    # Checking for word-by-word violations
    title_keywords = []
    ignore = ['with', 'of', 'and', 'or', 'to', 'the', 'a', 'an', 'at', 'for', 'in', 'over', 'on', 'iPhone',
              'iPad', 'by']
    num_lower_case = 0
    num_all_caps = 0
    num_incorrect_caps = 0
    contains_dollar_sign = False
    for word in title.split():
        word = re.sub('[^a-zA-Z0-9 \n.]', '', word)
        if word.lower() not in (item.lower() for item in ignore):
            title_keywords.append(word)

        # Checking for words not starting with upper case
        try:
            if word[0].islower() and word.lower() not in (word.lower() for word in ignore):
                num_lower_case += 1
        except IndexError:
            pass

        # Checking for any all caps words
        if word.isupper() and len(word) > 3:
            num_all_caps += 1

        # Checking for mis-capitalized conjunctions & articles
        try:
            if word[0].isupper() and word.lower() in ignore:
                num_incorrect_caps += 1
        except IndexError:
            pass

        # Checking for dollar sign $
        if '$' in word:
            contains_dollar_sign = True

    return({
        'title': title,
        'num_chars': num_chars,
        'num_chars_gte_sixty': num_chars_gte_sixty,
        'contains_promo_phrase': contains_promo_phrase,
        'contains_single_quote': contains_single_quote,
        'contains_ascii': contains_ascii,
        'contains_seo_adverse_chars': contains_seo_adverse_chars,
        'num_lower_case': num_lower_case,
        'num_all_caps': num_all_caps,
        'num_incorrect_caps': num_incorrect_caps,
        'contains_dollar_sign': contains_dollar_sign
    })


def analyze_description(description):
    # Checking for quotes
    if re.findall(r'\D\\[\"\']', description):
        contains_quotes = True
    else:
        contains_quotes = False

    # Check for HTML/JS in descriptions
    if bool(BeautifulSoup(description, "html.parser").find()):
        contains_html = True
    else:
        contains_html = False

    # Check for price/condition details
    flags = ['Mint Condition', 'Lowest price', 'Great Offer', 'Best Price',
             'Great Condition', 'Good Condition', 'Lowest Offer']
    if any(flag in description for flag in flags):
        contains_price_condition_info = True
    else:
        contains_price_condition_info = False

    # Check for shipping offers/details
    flags = ['Free Shipping', 'Fast Shipping', 'Day Shipping']
    if any(flag in description for flag in flags):
        contains_shipping_info = True
    else:
        contains_shipping_info = False

    # Check for contact info (phone #s, emails, websites, etc.)
    flags = ['@', '.com', '.org']
    if any(flag in description for flag in flags) or contains_phone_num(description):
        contains_contact_info = True
    else:
        contains_contact_info = False

    return({
        'char_count': len(description),
        'contains_quotes': contains_quotes,
        'contains_html': contains_html,
        'contains_price_condition_info': contains_price_condition_info,
        'contains_shipping_info': contains_shipping_info,
        'contains_contact_info': contains_contact_info,

    })


def analyze_bullets(feature_bullets):
    # Checking that bullets start with upper case
    num_lower_case_bullets = 0
    for bullet in feature_bullets:
        bullet = bullet.replace('\'', '')
        if bullet[0].islower() and bullet[0].isalpha():
            num_lower_case_bullets += 1

    num_bullets = len(feature_bullets)

    return({
        'num_lower_case_bullets': num_lower_case_bullets,
        'num_bullets': num_bullets
    })


def analyze_media(images, videos):
    num_images = len(images)
    num_videos = 0
    for video in videos:
        if video['vendor'] == "Manufacturer Video" or video['vendor'] == "Seller Video":
            num_videos += 1

    low_qual_images = 0
    high_whitespace_images = 0
    for image in images:
        width, height, whitespace = get_image_stats(image)
        if not width or not height or not whitespace:
            continue
        # Num images > 1000x1000px
        if width < 1000 and height < 1000:
            low_qual_images += 1
        # High whitespace images
        if whitespace >= 0.85:
            high_whitespace_images += 1

    return({
        'num_images': num_images,
        'low_qual_images': low_qual_images,
        'high_whitespace_images': high_whitespace_images,
        'num_videos': num_videos,
        'feature_image_url': images[0] if images else None,
    })


def calculate_product_scores(product):
    title_score = 0
    title = product['title']
    if title['num_lower_case'] <= 1:
        title_score += 5
    if title['num_all_caps'] < 1:
        title_score += 5
    if title['num_incorrect_caps'] < 1:
        title_score += 5
    if not title['contains_single_quote']:
        title_score += 5
    if not title['contains_seo_adverse_chars']:
        title_score += 5
    if not title['contains_ascii']:
        title_score += 5
    if not title['contains_promo_phrase']:
        title_score += 12
    if not title['contains_dollar_sign']:
        title_score += 8

    description_score = 0
    description = product['description']
    if description['char_count'] != 0:
        if description['char_count'] >= 250:
            description_score += 8
        if description['char_count'] >= 500:
            description_score += 7
        if description['char_count'] >= 1500:
            description_score += 5
        if 1600 <= description['char_count'] <= 2100:
            description_score += 5
        if not description['contains_quotes']:
            description_score += 5
        if not description['contains_html']:
            description_score += 5
        if not description['contains_price_condition_info']:
            description_score += 5
        if not description['contains_shipping_info']:
            description_score += 5
        if not description['contains_contact_info']:
            description_score += 15

    bullets_score = 0
    bullets = product['bullets']
    if bullets['num_bullets'] >= 3:
        bullets_score += 5
    if bullets['num_bullets'] >= 4:
        bullets_score += 10
    if bullets['num_bullets'] >= 5:
        bullets_score += 10
    if bullets['num_lower_case_bullets'] < 1:
        bullets_score += 10

    media_score = 0
    media = product['media']
    if media['num_images'] >= 5:
        media_score += 35
    if media['num_images'] >= 6:
        media_score += 15
    if media['num_images'] >= 7:
        media_score += 10
    if media['num_images'] >= 8:
        media_score += 5
    if media['num_images'] < 10:
        media_score += 10
    if media['low_qual_images'] < 1:
        media_score += 25
    if media['num_videos'] >= 1:
        media_score += 0

    ratings_and_reviews_score = 0
    ratings_and_reviews = product['ratings_and_reviews']
    if ratings_and_reviews['review_count'] >= 10:
        ratings_and_reviews_score += 5
    if ratings_and_reviews['review_count'] >= 25:
        ratings_and_reviews_score += 5
    if ratings_and_reviews['review_count'] >= 50:
        ratings_and_reviews_score += 5
    if ratings_and_reviews['review_count'] >= 100:
        ratings_and_reviews_score += 5
    if ratings_and_reviews['review_count'] >= 250:
        ratings_and_reviews_score += 5
    if ratings_and_reviews['rating'] >= 4.5:
        ratings_and_reviews_score += 20
    if ratings_and_reviews['rating'] >= 4.0:
        ratings_and_reviews_score += 30
    if ratings_and_reviews['rating'] >= 3.5:
        ratings_and_reviews_score += 15
    if ratings_and_reviews['rating'] >= 3.0:
        ratings_and_reviews_score += 10

    return({
        "title_score": title_score,
        "description_score": description_score,
        "bullets_score": bullets_score,
        "media_score": media_score,
        "ratings_and_reviews_score": ratings_and_reviews_score,
    })

