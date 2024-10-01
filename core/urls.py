from django.urls import path, include
# import django_eventstream
from .views import food_planer_request, sync_test_view



urlpatterns = [
    path('food_planer', food_planer_request, name='food_planer'),
    # path('test', async_test_view, name='test'),
    path('sync_test', sync_test_view, name='sync_test'),
    # path('rooms/<room_id>/events/', include(django_eventstream.urls), {
    #     'format-channels': ['room-{room_id}']
    # })
]