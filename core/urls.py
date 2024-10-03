from django.urls import path, include
# import django_eventstream
from .views import *



urlpatterns = [
    path('food_planner', food_planner_request, name='food_planner'),
    path('get_grocery_stores', get_grocery_stores, name='get_grocery_stores'),
    # path('test', async_test_view, name='test'),
    path('sync_test', sync_test_view, name='sync_test'),
    # path('rooms/<room_id>/events/', include(django_eventstream.urls), {
    #     'format-channels': ['room-{room_id}']
    # })
]