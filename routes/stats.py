from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import MealRecord, ActivityLog, BodyMeasurement, DietGoal, db
from datetime import datetime, date, timedelta

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/')
def stats():
    # Данные за последние 7 дней для графика калорий
    today = date.today()
    week = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [d.strftime('%d.%m') for d in week]

    calorie_intake = []
    calorie_burn = []
    for d in week:
        meals = MealRecord.query.filter(MealRecord.date == d).all()
        activities = ActivityLog.query.filter(ActivityLog.date == d).all()
        intake = sum(meal.total_calories() for meal in meals)
        burn = sum(a.calories_burned for a in activities)
        calorie_intake.append(round(intake, 1))
        calorie_burn.append(round(burn, 1))


    # Последние замеры тела (уже отсортированы от старых к новым)
    measurements = BodyMeasurement.query.order_by(BodyMeasurement.date.desc()).limit(10).all()
    measurements.reverse()

    # Прогресс веса
    weight_labels = [m.date.strftime('%d.%m') for m in measurements]
    weight_data = [m.weight for m in measurements]

    # Данные для обхватов (null для отсутствующих значений)
    chest_data = [m.chest if m.chest and m.chest > 0 else None for m in measurements]
    waist_data = [m.waist if m.waist and m.waist > 0 else None for m in measurements]
    hips_data = [m.hips if m.hips and m.hips > 0 else None for m in measurements]
    biceps_data = [m.biceps if m.biceps and m.biceps > 0 else None for m in measurements]

    return render_template('stats.html',
                           labels=labels,
                           calorie_intake=calorie_intake,
                           calorie_burn=calorie_burn,
                           measurements=measurements,
                           weight_labels=weight_labels,
                           weight_data=weight_data,
                           chest_data=chest_data,
                           waist_data=waist_data,
                           hips_data=hips_data,
                           biceps_data=biceps_data,
                           today=date.today())


@stats_bp.route('/add-measurement', methods=['POST'])
def add_measurement():
    """Добавление нового замера тела"""
    try:
        measurement_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        measurement_date = date.today()

    measurement = BodyMeasurement(
        date=measurement_date,
        weight=float(request.form.get('weight', 0)),
        chest=float(request.form.get('chest', 0)),
        waist=float(request.form.get('waist', 0)),
        hips=float(request.form.get('hips', 0)),
        biceps=float(request.form.get('biceps', 0)),
        notes=request.form.get('notes', '')
    )
    db.session.add(measurement)
    db.session.commit()
    flash('Замер добавлен!', 'success')
    return redirect(url_for('stats.stats'))


@stats_bp.route('/delete-measurement/<int:measurement_id>', methods=['POST'])
def delete_measurement(measurement_id):
    """Удаление замера"""
    measurement = BodyMeasurement.query.get_or_404(measurement_id)
    db.session.delete(measurement)
    db.session.commit()
    flash('Замер удалён', 'success')
    return redirect(url_for('stats.stats'))