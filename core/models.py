from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # ⭐ NEW FIELDS
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    gender = models.CharField(max_length=10, default="male") 
    diet_type = models.CharField(max_length=10, default="veg")

    age = models.IntegerField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    goal = models.CharField(max_length=20, default="maintain")
    health_conditions = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)

    role = models.CharField(max_length=20, default="user")
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class BMI(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    height = models.FloatField()
    weight = models.FloatField()
    age = models.IntegerField()
    bmi_value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.email} - BMI {self.bmi_value}"


class DietPlan(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    week_plan = models.TextField()

    # ⭐ FAVORITE SUPPORT
    is_favorite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diet Plan for {self.user.user.email}"


class AIUsage(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.email} - {self.created_at}"


class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


class FavoriteMeal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_name = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=50)  # breakfast/lunch/dinner
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.meal_name}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.diet_plan.id}"