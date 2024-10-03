from rest_framework.renderers import BrowsableAPIRenderer

class FoodPlanerPostRenderer(BrowsableAPIRenderer):
    template = 'food_planner_request.html'

class LocationInfoPostRenderer(BrowsableAPIRenderer):
    template = 'location_info_request.html'