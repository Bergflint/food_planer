from rest_framework.renderers import BrowsableAPIRenderer

class FoodPlanerPostRenderer(BrowsableAPIRenderer):
    template = 'food_planer_request.html'