from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

from datetime import timedelta
import random

from .models import (
    UserProfile,
    BMI,
    DietPlan,
    AIUsage,
    EmailOTP,
    FavoriteMeal
)

from .serializers import (
    UserProfileSerializer,
    FavoriteMealSerializer
)

from .ai_service import AIDietGenerator


# =========================
# HELPER
# =========================

def is_admin(user):
    try:
        return user.profile.role == "admin"
    except:
        return False


# =========================
# BMI
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_bmi(request):

    height = float(request.data.get('height'))
    weight = float(request.data.get('weight'))
    age = int(request.data.get('age'))

    bmi_value = weight / ((height / 100) ** 2)

    profile, created = UserProfile.objects.get_or_create(user=request.user)

    BMI.objects.create(
        user=profile,
        height=height,
        weight=weight,
        age=age,
        bmi_value=round(bmi_value, 2)
    )

    return Response({
        "message": "BMI calculated",
        "bmi": round(bmi_value, 2)
    })


# =========================
# GENERATE DIET
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_diet(request):

    try:

        profile = UserProfile.objects.get(user=request.user)

        if profile.is_banned:
            return Response({"error": "Account banned"}, status=403)

        bmi = request.data.get('bmi')
        craving = request.data.get('craving', "")

        age = profile.age
        height = profile.height
        weight = profile.weight
        goal = profile.goal
        gender = profile.gender
        diet_type = profile.diet_type
        health_conditions = profile.health_conditions or ""
        allergies = profile.allergies or ""

        diet_text = AIDietGenerator.generate_diet(
            email=request.user.email,
            age=age,
            height=height,
            weight=weight,
            bmi=bmi,
            goal=goal,
            gender=gender,
            diet_type=diet_type,
            health_conditions=health_conditions,
            allergies=allergies,
            craving=craving
        )

        diet = DietPlan.objects.create(
            user=profile,
            week_plan=diet_text
        )

        AIUsage.objects.create(user=profile)

        return Response({
            "message": "Diet plan generated",
            "diet_plan": diet_text,
            "plan_id": diet.id,
            "is_favorite": diet.is_favorite
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)


# =========================
# PROFILE
# =========================

class UserProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Serialize profile data
        serializer = UserProfileSerializer(profile)

        data = serializer.data

        # ✅ ADD USER INFO (FIX)
        data["name"] = request.user.first_name or "User"
        data["email"] = request.user.email
        data["username"] = request.user.username

        return Response(data)


    def post(self, request):

        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # ✅ SAVE NAME
        name = request.data.get("name")
        if name:
            request.user.first_name = name
            request.user.save()
            profile.name = name

        # ✅ SAVE PHONE
        phone = request.data.get("phone_number")
        if phone:
            profile.phone_number = phone

        # ✅ SAVE OTHER FIELDS ONLY
        serializer = UserProfileSerializer(
            profile,
            data={
                "age": request.data.get("age"),
                "height": request.data.get("height"),
                "weight": request.data.get("weight"),
                "goal": request.data.get("goal"),
                "health_conditions": request.data.get("health_conditions"),
                "allergies": request.data.get("allergies"),
                "gender": request.data.get("gender"),
                "diet_type": request.data.get("diet_type"),
            },
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

        profile.save()   # 🔥 FINAL SAVE (IMPORTANT)

        return Response({"message": "Profile updated"})


# =========================
# USER DIETS
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_diets(request):

    profile = request.user.profile

    diets = DietPlan.objects.filter(user=profile).order_by('-created_at')[:4]

    data = []

    for diet in diets:
        data.append({
            "id": diet.id,
            "week_plan": diet.week_plan,
            "created_at": diet.created_at.strftime("%d %b %Y")
        })

    return Response(data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_plan(request, id):

    try:

        plan = DietPlan.objects.get(id=id, user=request.user.profile)

        plan.delete()

        return Response({"message": "Plan deleted successfully"})

    except DietPlan.DoesNotExist:

        return Response({"error": "Plan not found"}, status=404)


# =========================
# FAVORITES
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, id):

    plan = DietPlan.objects.get(id=id, user=request.user.profile)

    plan.is_favorite = not plan.is_favorite
    plan.save()

    return Response({
        "message": "Favorite updated",
        "is_favorite": plan.is_favorite
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorites(request):

    profile = request.user.profile

    plans = DietPlan.objects.filter(
        user=profile,
        is_favorite=True
    ).order_by('-created_at')

    data = []

    for plan in plans:
        data.append({
            "id": plan.id,
            "week_plan": plan.week_plan,
            "created_at": plan.created_at.strftime("%d %b %Y")
        })

    return Response(data)


# =========================
# AI CHAT
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nutrition_chat(request):

    message = request.data.get("message")

    profile = request.user.profile

    latest_diet = DietPlan.objects.filter(
        user=profile
    ).order_by("-created_at").first()

    diet_text = latest_diet.week_plan if latest_diet else ""

    reply = AIDietGenerator.chat_with_ai(
        message=message,
        age=profile.age,
        height=profile.height,
        weight=profile.weight,
        goal=profile.goal,
        health_conditions=profile.health_conditions,
        allergies=profile.allergies,
        diet_plan=diet_text
    )

    return Response({"reply": reply})


# =========================
# CRAVING SNACK
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def craving_snack(request):

    craving = request.data.get("craving")

    snack = AIDietGenerator.generate_craving_snack(craving)

    return Response({"snack": snack})


# =========================
# BMI HISTORY
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bmi_history(request):

    profile = request.user.profile

    records = BMI.objects.filter(user=profile).order_by('-created_at')

    data = []

    for r in records:
        data.append({
            "height": r.height,
            "weight": r.weight,
            "age": r.age,
            "bmi": r.bmi_value,
            "date": r.created_at.strftime("%d %b %Y")
        })

    return Response(data)


# =========================
# OTP SIGNUP
# =========================

@api_view(['POST'])
def send_otp(request):

    email = request.data.get("email")

    if not email:
        return Response({"error": "Email is required"}, status=400)

    otp = str(random.randint(100000, 999999))

    # Delete old OTP if exists
    EmailOTP.objects.filter(email=email).delete()

    # Save new OTP
    EmailOTP.objects.create(email=email, otp=otp)

    # ================= EMAIL CONTENT =================

    subject = "NutriGuide Verification Code"

    text_content = f"Your OTP is {otp}"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f7fb;">
      
      <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 25px;">

        <h2 style="color: #2e7d32;">NutriGuide 🔥</h2>

        <p style="font-size: 16px;">Hello 👋,</p>

        <p style="font-size: 15px; color: #555;">
          Welcome to <b>NutriGuide</b> — your AI-powered nutrition companion.
        </p>

        <p style="font-size: 15px; color: #555;">
          Please use the OTP below to verify your account:
        </p>

        <div style="text-align: center; margin: 25px 0;">
          <span style="font-size: 30px; letter-spacing: 5px; font-weight: bold; color: #2e7d32;">
            {otp}
          </span>
        </div>

        <p style="font-size: 14px; color: #777;">
          ⏳ This OTP will expire in 5 minutes.
        </p>

        <hr style="margin: 20px 0;">

        <p style="font-size: 13px; color: #aaa;">
          If you didn’t request this, you can safely ignore this email.
        </p>

        <p style="font-size: 13px; color: #aaa;">
          — Team NutriGuide 💚
        </p>

      </div>

    </div>
    """

    # ================= SEND EMAIL =================

    email_message = EmailMultiAlternatives(
        subject,
        text_content,
        "NutriGuide Support <nutriguide.support@gmail.com>",
        [email],
    )

    email_message.attach_alternative(html_content, "text/html")
    email_message.send()

    return Response({"message": "OTP sent successfully"})


@api_view(['POST'])
def verify_otp(request):

    name = request.data.get("name")
    email = request.data.get("email")
    otp = request.data.get("otp")
    password = request.data.get("password")
    phone = request.data.get("phone_number")   # 🔥 ADD THIS

    print("OTP REGISTER NAME:", name)
    print("PHONE:", phone)

    record = EmailOTP.objects.filter(email=email).last()

    if not record or record.otp != otp:
        return Response({"error": "Invalid OTP"}, status=400)

    # ✅ CREATE USER WITH NAME
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name
    )

    # 🔥 CREATE PROFILE WITH NAME + PHONE
    UserProfile.objects.create(
        user=user,
        name=name,
        phone_number=phone
    )

    record.delete()

    return Response({"message": "Account created"}) 

# ==============================
# ADMIN: Get All Users
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_users(request):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    profiles = UserProfile.objects.select_related("user").all()

    data = []

    for profile in profiles:
        data.append({
            "id": profile.user.id,
            "email": profile.user.email,
            "name": profile.name,
            "phone_number": profile.phone_number,
            "age": profile.age,
            "height": profile.height,
            "weight": profile.weight,
            "goal": profile.goal,
            "role": profile.role,
            "is_banned": profile.is_banned
        })

    return Response(data)


# ==============================
# ADMIN: SYSTEM STATS
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    total_users = UserProfile.objects.count()
    total_diets = DietPlan.objects.count()
    total_ai_calls = AIUsage.objects.count()
    banned_users = UserProfile.objects.filter(is_banned=True).count()

    return Response({
        "total_users": total_users,
        "total_diets": total_diets,
        "total_ai_calls": total_ai_calls,
        "banned_users": banned_users
    })


# ==============================
# ADMIN: TOGGLE BAN
# ==============================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_toggle_ban(request, user_id):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    try:

        profile = UserProfile.objects.get(user__id=user_id)

        profile.is_banned = not profile.is_banned
        profile.save()

        return Response({
            "message": "Ban status updated",
            "is_banned": profile.is_banned
        })

    except UserProfile.DoesNotExist:

        return Response({"error": "User not found"}, status=404)

# ==============================
# ADMIN: HEALTH CONDITION STATS
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_health_stats(request):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    profiles = UserProfile.objects.exclude(health_conditions="")

    stats = {}

    for profile in profiles:

        condition = profile.health_conditions.strip().lower()

        if condition not in stats:
            stats[condition] = 1
        else:
            stats[condition] += 1

    return Response(stats)

# ==============================
# ADMIN: AI USAGE PER USER
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_ai_usage(request):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    usage_entries = AIUsage.objects.select_related("user__user")

    data = {}

    for entry in usage_entries:

        email = entry.user.user.email

        if email not in data:
            data[email] = 1
        else:
            data[email] += 1

    return Response(data)

# ==============================
# ADMIN: GET ALL DIET PLANS
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_diets(request):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    diets = DietPlan.objects.select_related("user__user").all().order_by("-created_at")

    data = []

    for diet in diets:
        data.append({
            "id": diet.id,
            "user": diet.user.user.email,
            "plan": diet.week_plan,
            "created_at": diet.created_at
        })

    return Response(data)

# ==============================
# ADMIN: GET SINGLE USER DETAILS
# ==============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_details(request, user_id):

    if not is_admin(request.user):
        raise PermissionDenied("Admin access required")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    profile = UserProfile.objects.filter(user=user).first()

    return Response({
        "name": profile.name if profile else None,
        "email": user.email,
        "phone_number": profile.phone_number if profile else None,
        "age": profile.age if profile else None,
        "height": profile.height if profile else None,
        "weight": profile.weight if profile else None,
        "goal": profile.goal if profile else None,
        "health_conditions": profile.health_conditions if profile else None,
        "allergies": profile.allergies if profile else None,
        "role": profile.role if profile else "user",
        "is_banned": profile.is_banned if profile else False,
    })
