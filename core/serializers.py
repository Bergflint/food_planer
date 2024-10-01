from rest_framework import serializers



class FoodPlanerSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance = serializers.IntegerField()
    budget = serializers.IntegerField()
    portions = serializers.IntegerField()

    class Meta:
        fields = ['latitude', 'longitude', 'distance', 'budget', 'portions']