"""
Django settings for listing_grader project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-g+ln+)t==jgw!tne^3^u4-09q_d_!$pw6o(7m3-agj(k+z^-c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['45.55.104.61', '127.0.0.1', 'insights.zentail.com', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'background_task',
    'app.apps.AppConfig',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'listing_grader.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'listing_grader.wsgi.application'

CORS_ORIGIN_WHITELIST = [
    "https://gradier.webflow.io",
    "https://zentail-site-10-18-update.webflow.io",
    "https://www.zentail.com"

]

CSRF_TRUSTED_ORIGINS = [
    'gradier.webflow.io',
    'zentail-site-10-18-update.webflow.io',
    'www.zentail.com'

]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'listing_grader_django.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'


# Project specific settings
SUBMISSIONS_TIMEDELTA_DAYS = 7
SUBMISSIONS_ALLOWED = 2

ZINC_SELLER_API_URL = 'https://api.zinc.io/v1/search'
ZINC_PRODUCT_API_URL = 'https://api.zinc.io/v1/products/'
ZINC_API_TOKEN = 'EE4CB9F7EC5F0B8CCECD89B8'

WEBFLOW_TOKEN = '7626821a1e1e278cd5ae07a1c15f057dd4d25ef68d2cf34ece7863c0db59572d'
#WEBFLOW_TOKEN = '01644e575106ed6302ecdda52dd8e1bb0d60757a16f4c4b9597fc1a65ca90c90'
WEBFLOW_SITE_ID = '5bbe02f84941df1b66dda9b5'
#WEBFLOW_SITE_ID = '5d60672844a280322e776b37'
WEBFLOW_COLLECTION = '5e2861c48f10441879f85948'
#WEBFLOW_COLLECTION = '5db07b5331da36426bfa34f1'
WEBFLOW_DEFAULT_ENDPOINT = 'https://api.webflow.com'
WEBFLOW_VERSION = '1.0.0'

ZAPIER_WEBHOOK = 'https://hooks.zapier.com/hooks/catch/92396/otksap7/'

MAX_ATTEMPTS = 2