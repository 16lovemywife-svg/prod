from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import (
    MealRecord, MealEntry, Recipe, Product, DietGoal,
    UserProfile, ActivityLog, db
)
from services.nutrition import calculate_recipe_nutrition
from services.activity import calculate_calories_burned
from datetime import datetime, date, time, timedelta
from sqlalchemy import func

diary_bp = Blueprint('diary', __name__)


@diary_bp.route('/')
def diary():
    """Главная страница дневника с выбором даты и итогами"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        diary_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        diary_date = date.today()

    prev_date = diary_date - timedelta(days=1)
    next_date = diary_date + timedelta(days=1)

    meals = MealRecord.query.filter(MealRecord.date == diary_date).order_by(MealRecord.time).all()
    activities = ActivityLog.query.filter(ActivityLog.date == diary_date).all()

    goal = DietGoal.query.first()
    if not goal:
        goal = DietGoal()
        db.session.add(goal)
        db.session.commit()

    user_profile = UserProfile.query.first()
    if not user_profile:
        user_profile = UserProfile()
        db.session.add(user_profile)
        db.session.commit()

    total_calories = sum(meal.total_calories() for meal in meals)
    total_proteins = sum(meal.total_proteins() for meal in meals)
    total_fats = sum(meal.total_fats() for meal in meals)
    total_carbs = sum(meal.total_carbs() for meal in meals)

    burned_calories = sum(a.calories_burned for a in activities)

    # Расчёт TDEE на основе профиля
    tdee = None
    if user_profile.weight > 0 and user_profile.height > 0 and user_profile.age > 0:
        if user_profile.gender == 'male':
            bmr = 10 * user_profile.weight + 6.25 * user_profile.height - 5 * user_profile.age + 5
        else:
            bmr = 10 * user_profile.weight + 6.25 * user_profile.height - 5 * user_profile.age - 161
        factors = {'low': 1.2, 'medium': 1.55, 'high': 1.725}
        tdee = bmr * factors.get(user_profile.activity_level, 1.55)

    # Рекомендуемое потребление с учётом цели и активности
    recommended_intake = None
    if tdee:
        if goal.goal_type == 'lose':
            recommended_intake = (tdee + burned_calories) - (tdee * 0.2)
        elif goal.goal_type == 'gain':
            recommended_intake = (tdee + burned_calories) + (tdee * 0.1)
        else:
            recommended_intake = tdee + burned_calories

    net_balance = (total_calories - recommended_intake) if recommended_intake is not None else None

    return render_template(
        'diary.html',
        date=diary_date,
        prev_date=prev_date,
        next_date=next_date,
        now=datetime.now(),
        meals=meals,
        goal=goal,
        totals={
            'calories': total_calories,
            'proteins': total_proteins,
            'fats': total_fats,
            'carbs': total_carbs,
            'burned': burned_calories,
            'tdee': tdee,
            'recommended': recommended_intake,
            'balance': net_balance,
            'net_balance': net_balance
        }
    )


@diary_bp.route('/add-meal', methods=['POST'])
def add_meal():
    """Добавление нового приёма пищи"""
    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    meal_type = request.form.get('meal_type', 'завтрак')
    time_str = request.form.get('time', datetime.now().strftime('%H:%M'))

    try:
        meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        meal_date = date.today()
    try:
        meal_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        meal_time = datetime.now().time()

    meal = MealRecord(date=meal_date, meal_type=meal_type, time=meal_time)
    db.session.add(meal)
    db.session.commit()
    flash('Приём пищи добавлен!', 'success')
    return redirect(url_for('diary.diary', date=date_str))


@diary_bp.route('/add-entry/<int:meal_id>', methods=['POST'])
def add_entry(meal_id):
    """Добавление позиции в приём пищи (продукт или рецепт)"""
    meal = MealRecord.query.get_or_404(meal_id)
    entry_type = request.form.get('entry_type')
    quantity = float(request.form.get('quantity', 1))

    if entry_type == 'recipe':
        recipe_id = int(request.form.get('recipe_id'))
        entry = MealEntry(
            meal_id=meal.id,
            entry_type='recipe',
            recipe_id=recipe_id,
            quantity=quantity  # теперь это граммы готового блюда
        )
    elif entry_type == 'product':
        product_id = int(request.form.get('product_id'))
        entry = MealEntry(
            meal_id=meal.id,
            entry_type='product',
            product_id=product_id,
            quantity=quantity  # граммы продукта
        )
    else:
        flash('Неверный тип записи', 'error')
        return redirect(url_for('diary.diary', date=meal.date.strftime('%Y-%m-%d')))

    db.session.add(entry)
    db.session.commit()
    flash('Запись добавлена', 'success')
    return redirect(url_for('diary.diary', date=meal.date.strftime('%Y-%m-%d')))


@diary_bp.route('/edit-entry/<int:entry_id>', methods=['POST'])
def edit_entry(entry_id):
    """Редактирование количества позиции"""
    entry = MealEntry.query.get_or_404(entry_id)
    quantity = float(request.form.get('quantity', entry.quantity))
    entry.quantity = quantity
    db.session.commit()
    flash('Количество обновлено', 'success')
    return redirect(url_for('diary.diary', date=entry.meal.date.strftime('%Y-%m-%d')))


@diary_bp.route('/delete-entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry = MealEntry.query.get_or_404(entry_id)
    meal_date = entry.meal.date
    db.session.delete(entry)
    db.session.commit()
    flash('Позиция удалена', 'success')
    return redirect(url_for('diary.diary', date=meal_date.strftime('%Y-%m-%d')))


@diary_bp.route('/delete-meal/<int:meal_id>', methods=['POST'])
def delete_meal(meal_id):
    meal = MealRecord.query.get_or_404(meal_id)
    meal_date = meal.date
    db.session.delete(meal)
    db.session.commit()
    flash('Приём пищи удалён', 'success')
    return redirect(url_for('diary.diary', date=meal_date.strftime('%Y-%m-%d')))


@diary_bp.route('/update-goals', methods=['POST'])
def update_goals():
    """Обновление целей по питанию"""
    goal = DietGoal.query.first()
    if not goal:
        goal = DietGoal()
        db.session.add(goal)

    goal.calories = float(request.form.get('calories', goal.calories))
    goal.proteins = float(request.form.get('proteins', goal.proteins))
    goal.fats = float(request.form.get('fats', goal.fats))
    goal.carbs = float(request.form.get('carbs', goal.carbs))
    goal.goal_type = request.form.get('goal_type', goal.goal_type)

    db.session.commit()
    flash('Цели обновлены!', 'success')
    return redirect(url_for('diary.diary'))


@diary_bp.route('/calculate-goals', methods=['POST'])
def calculate_goals():
    """Автоматический расчёт целей на основе профиля и цели"""
    profile = UserProfile.query.first()
    if not profile:
        return jsonify({'error': 'profile_not_found'}), 400

    if profile.weight <= 0 or profile.height <= 0 or profile.age <= 0:
        return jsonify({'error': 'invalid_profile'}), 400

    goal_type = request.json.get('goal_type', 'maintain')

    if profile.gender == 'male':
        bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
    else:
        bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161

    factors = {'low': 1.2, 'medium': 1.55, 'high': 1.725}
    tdee = bmr * factors.get(profile.activity_level, 1.55)

    if goal_type == 'lose':
        calories = tdee * 0.8
    elif goal_type == 'gain':
        calories = tdee * 1.1
    else:
        calories = tdee

    calories = round(calories)
    proteins = round((calories * 0.30) / 4, 1)
    fats = round((calories * 0.30) / 9, 1)
    carbs = round((calories * 0.40) / 4, 1)

    print(f"DEBUG: goal_type={goal_type}, tdee={tdee:.1f}, calories={calories}")

    return jsonify({
        'calories': calories,
        'proteins': proteins,
        'fats': fats,
        'carbs': carbs
    })


@diary_bp.route('/add-recipe-to-meal', methods=['POST'])
def add_recipe_to_meal():
    """Добавление рецепта в дневник как приём пищи (по граммам)"""
    recipe_id = int(request.form.get('recipe_id'))
    meal_type = request.form.get('meal_type', 'завтрак')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    weight_grams = float(request.form.get('weight_grams', 100))

    try:
        meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        meal_date = date.today()

    try:
        meal_time = datetime.strptime(time_str, '%H:%M').time()
    except (ValueError, TypeError):
        meal_time = datetime.now().time()

    recipe = Recipe.query.get_or_404(recipe_id)

    meal = MealRecord(
        date=meal_date,
        meal_type=meal_type,
        time=meal_time
    )
    db.session.add(meal)
    db.session.flush()

    entry = MealEntry(
        meal_id=meal.id,
        entry_type='recipe',
        recipe_id=recipe.id,
        quantity=weight_grams  # сохраняем граммы
    )
    db.session.add(entry)
    db.session.commit()

    flash(f'Рецепт "{recipe.title}" добавлен ({weight_grams} г)', 'success')
    return redirect(url_for('diary.diary', date=date_str))