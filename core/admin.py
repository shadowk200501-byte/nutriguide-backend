from django.contrib import admin
from .models import UserProfile, BMI, DietPlan, AIUsage


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("get_name", "user", "age", "goal", "is_banned")

    def get_name(self, obj):
        return obj.user.first_name   # 🔥 fetch name from User model

    get_name.short_description = "Name"


@admin.register(BMI)
class BMIAdmin(admin.ModelAdmin):
    list_display = ("user", "bmi_value", "created_at")


@admin.register(DietPlan)
class DietPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "short_plan", "created_at", "is_favorite")

    search_fields = ("user__email", "week_plan")   # 🔥 ADD THIS
    list_filter = ("is_favorite",)  

    def short_plan(self, obj):
        return obj.week_plan[:60] if obj.week_plan else "No Plan"

    short_plan.short_description = "Diet Plan"


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
