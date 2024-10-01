from rest_framework.renderers import BrowsableAPIRenderer

class FoodPlanerPostRenderer(BrowsableAPIRenderer):
    template = 'food_planner_request.html'