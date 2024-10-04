from rest_framework import serializers



class FoodPlanerSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance = serializers.IntegerField()
    budget = serializers.IntegerField()
    portions = serializers.IntegerField()

    class Meta:
        fields = ['latitude', 'longitude', 'distance', 'budget', 'portions']

class LocationInfoSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance = serializers.FloatField()

    class Meta:
        fields = ['latitude', 'longitude', 'distance']

class FindDishesSerializer(serializers.Serializer):
    selectedStores = serializers.ListField(child=serializers.CharField()) #A list with all the places ID
    foodPreferences = serializers.ListField(child=serializers.CharField()) #A list with all the food preferences
    latitude = serializers.CharField()
    longitude = serializers.CharField()

    class Meta:
        fields = ['selectedStores', 'foodPreferences', 'latitude', 'longitude']