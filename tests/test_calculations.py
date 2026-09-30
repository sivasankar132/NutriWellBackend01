import pytest
from app.utils.calculations import (
    calculate_bmi,
    calculate_bmr,
    calculate_tdee,
    calculate_macro_targets,
    aggregate_meal_nutrition
)

def test_bmi_calculation():
    res = calculate_bmi(70, 175)
    assert res["bmi"] == 22.86
    assert res["category"] == "Normal weight"

    overweight = calculate_bmi(90, 170)
    assert overweight["bmi"] == 31.14
    assert overweight["category"] == "Obesity"

def test_bmr_calculation():
    # Male 70kg, 175cm, 25 years: 10*70 + 6.25*175 - 5*25 + 5 = 700 + 1093.75 - 125 + 5 = 1673.75
    bmr_male = calculate_bmr(70, 175, 25, "Male")
    assert bmr_male == 1673.75

    # Female 60kg, 160cm, 28 years: 10*60 + 6.25*160 - 5*28 - 161 = 600 + 1000 - 140 - 161 = 1299.0
    bmr_female = calculate_bmr(60, 160, 28, "Female")
    assert bmr_female == 1299.0

def test_tdee_calculation():
    bmr = 1600.0
    tdee_mod = calculate_tdee(bmr, "Moderately Active")
    assert tdee_mod == 2480.0

def test_macro_targets_weight_loss():
    targets = calculate_macro_targets(2200.0, "weight_loss", 75.0)
    assert targets["daily_calorie_target"] == 1750.0
    assert targets["daily_protein_target"] >= 130.0
    assert targets["daily_water_target_ml"] >= 2000.0

def test_aggregate_meal_nutrition():
    items = [
        {"food_name": "Boiled Egg", "quantity": 2, "calories": 78, "protein": 6.3, "carbs": 0.6, "fats": 5.3, "fiber": 0, "cost_inr": 14},
        {"food_name": "Roti", "quantity": 2, "calories": 104, "protein": 3.1, "carbs": 21.0, "fats": 0.5, "fiber": 3.2, "cost_inr": 10}
    ]
    totals = aggregate_meal_nutrition(items)
    assert totals["calories"] == 364.0
    assert totals["protein"] == 18.8
    assert totals["carbs"] == 43.2
    assert totals["cost_inr"] == 48.0
