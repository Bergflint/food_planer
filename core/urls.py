from django.urls import path, include
# import django_eventstream
from .views import *
import django_eventstream


urlpatterns = [
    path('food_planner', food_planner_request, name='food_planner'),
    path('get_grocery_stores', get_grocery_stores, name='get_grocery_stores'),
    path('sync_test', sync_test_view, name='sync_test'),
    path('rooms/<room_id>/events/', include(django_eventstream.urls), {
        'format-channels': ['room-{room_id}']
    })
]