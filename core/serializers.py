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
    store_ids = serializers.ListField(child=serializers.CharField()) #A list with all the places ID

    class Meta:
        fields = ['store_ids']