from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import MealRecord, MealEntry, Recipe, Product, DietGoal, db
from services.nutrition import calculate_recipe_nutrition
import json
from datetime import datetime, date, time, timedelta
diary_bp = Blueprint('diary', __name__)


@diary_bp.route('/')
def diary():
    """Главная страница дневника с выбором даты"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        diary_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        diary_date = date.today()

    prev_date = diary_date - timedelta(days=1)
    next_date = diary_date + timedelta(days=1)

    meals = MealRecord.query.filter(MealRecord.date == diary_date).order_by(MealRecord.time).all()

    goal = DietGoal.query.first()
    if not goal:
        goal = DietGoal()
        db.session.add(goal)
        db.session.commit()

    total_calories = sum(meal.total_calories() for meal in meals)
    total_proteins = sum(meal.total_proteins() for meal in meals)
    total_fats = sum(meal.total_fats() for meal in meals)
    total_carbs = sum(meal.total_carbs() for meal in meals)

    return render_template('diary.html',
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
                               'carbs': total_carbs
                           })


@diary_bp.route('/add-meal', methods=['POST'])
def add_meal():
    """Добавление нового приёма пищи"""
    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    meal_type = request.form.get('meal_type', 'завтрак')
    time_str = request.form.get('time', datetime.now().strftime('%H:%M'))

    try:
        diary_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        diary_date = date.today()
    try:
        meal_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        meal_time = datetime.now().time()

    meal = MealRecord(date=diary_date, meal_type=meal_type, time=meal_time)
    db.session.add(meal)
    db.session.commit()
    flash('Приём пищи добавлен!', 'success')
    return redirect(url_for('diary.diary', date=date_str))


@diary_bp.route('/add-entry/<int:meal_id>', methods=['POST'])
def add_entry(meal_id):
    """Добавление позиции в приём пищи"""
    meal = MealRecord.query.get_or_404(meal_id)
    entry_type = request.form.get('entry_type')  # 'recipe' или 'product'
    quantity = float(request.form.get('quantity', 1))

    if entry_type == 'recipe':
        recipe_id = int(request.form.get('recipe_id'))
        entry = MealEntry(meal_id=meal.id, entry_type='recipe', recipe_id=recipe_id, quantity=quantity)
    elif entry_type == 'product':
        product_id = int(request.form.get('product_id'))
        entry = MealEntry(meal_id=meal.id, entry_type='product', product_id=product_id, quantity=quantity)
    else:
        flash('Неверный тип записи', 'error')
        return redirect(url_for('diary.diary', date=meal.date.strftime('%Y-%m-%d')))

    db.session.add(entry)
    db.session.commit()
    flash('Блюдо/продукт добавлен в приём пищи', 'success')
    return redirect(url_for('diary.diary', date=meal.date.strftime('%Y-%m-%d')))


@diary_bp.route('/edit-entry/<int:entry_id>', methods=['POST'])
def edit_entry(entry_id):
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


@diary_bp.route('/goals', methods=['POST'])
def update_goals():
    goal = DietGoal.query.first()
    if not goal:
        goal = DietGoal()
        db.session.add(goal)

    goal.calories = float(request.form.get('calories', goal.calories))
    goal.proteins = float(request.form.get('proteins', goal.proteins))
    goal.fats = float(request.form.get('fats', goal.fats))
    goal.carbs = float(request.form.get('carbs', goal.carbs))
    db.session.commit()
    flash('Цели обновлены!', 'success')
    return redirect(url_for('diary.diary'))