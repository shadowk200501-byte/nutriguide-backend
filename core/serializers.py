from rest_framework import serializers
from .models import UserProfile, BMI, FavoriteMeal

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class BMISerializer(serializers.ModelSerializer):
    class Meta:
        model = BMI
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['name','phone_number','age', 'height', 'weight','gender','diet_type','goal','health_conditions', 'allergies','role']

class FavoriteMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteMeal
        fields = '__all__'