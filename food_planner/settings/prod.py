from .common import * 


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
if os.environ.get('DJANGO_SECRET_KEY'):
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
else:
    SECRET_KEY = 'django-insecure-h$awk!rn+dn6$a8$6xu8d(skuzgr*4(gvo9o^^q=vm(39l8y20'

BASE_URL = 'http://127.0.0.1:8000'


REDIS_URL = 'redis://redis:6379/1'

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
        },
    },
}


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True 
}