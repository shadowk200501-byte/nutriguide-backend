import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class AIDietGenerator:

    @staticmethod
    def generate_diet(email, age, height, weight, bmi, goal,gender,diet_type, health_conditions, allergies, craving):

        prompt_template = PromptTemplate(
            input_variables=[
                "age",
                "height",
                "weight",
                "bmi",
                "goal",
                "gender",
                "diet_type",
                "health_conditions",
                "allergies",
                "craving",
            ],
            template="""
You are a certified professional Indian nutritionist AI.

Create a healthy 7-day Indian diet plan for the user.

User Details:
Age: {age}
Gender: {gender}
Height: {height} cm
Weight: {weight} kg
BMI: {bmi}
Goal: {goal}
Diet Type: {diet_type}
Health Conditions: {health_conditions}
Allergies: {allergies}
Today's craving: {craving}

Diet Rules:
- If goal is 'loss', create calorie deficit meals.
- If goal is 'gain', create calorie surplus meals.
- If goal is 'maintain', create balanced meals.
- Avoid all allergy foods.
- Adjust meals according to health conditions.
- Use common Indian foods (dal, roti, sabzi, rice, paneer, eggs, chicken, poha, idli, dosa, oats).
- Meals should be healthy and simple.
- If diet type is veg, DO NOT include eggs, chicken, fish, or meat.
- If diet type is nonveg, you may include eggs, chicken, fish, etc.

Return the diet EXACTLY in this format:

Today's craving: {craving}

Monday
Breakfast:
Lunch:
Dinner:
Snacks:

Tuesday
Breakfast:
Lunch:
Dinner:
Snacks:

Wednesday
Breakfast:
Lunch:
Dinner:
Snacks:

Thursday
Breakfast:
Lunch:
Dinner:
Snacks:

Friday
Breakfast:
Lunch:
Dinner:
Snacks:

Saturday
Breakfast:
Lunch:
Dinner:
Snacks:

Sunday
Breakfast:
Lunch:
Dinner:
Snacks:
"""
        )

        final_prompt = prompt_template.format(
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

        print("Calling Gemini 2.5 Flash...")

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        response = model.generate_content(final_prompt)

        print("Gemini responded successfully")

        return response.text.strip()

    @staticmethod
    def chat_with_ai(message, age, height, weight, goal, health_conditions, allergies, diet_plan):

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt = f"""
You are NutriGuide AI, a professional nutrition assistant.

User Profile:
Age: {age}
Height: {height}
Weight: {weight}
Goal: {goal}
Health Conditions: {health_conditions}
Allergies: {allergies}

Current Diet Plan:
{diet_plan}

User Question:
{message}

Give a helpful personalized answer based on the user's profile and diet plan.
"""

        response = model.generate_content(prompt)

        return response.text.strip()

    @staticmethod
    def generate_craving_snack(craving):

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt = f"""
You are a professional nutritionist AI.

User is craving: {craving}

Suggest a healthy snack alternative.

Return EXACTLY in this format:

Snack Name:
Recipe:
Calories:
Best Time To Eat:
"""

        response = model.generate_content(prompt)

        return response.text.strip()