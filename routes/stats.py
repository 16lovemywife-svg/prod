from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import MealRecord, ActivityLog, BodyMeasurement, DietGoal, db
from datetime import datetime, date, timedelta

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/')
def stats():
    today = date.today()
    period = request.args.get('period', '7')  # 7, 30, 90, all

    # Определяем начальную дату в зависимости от периода
    if period == '7':
        start_date = today - timedelta(days=6)
    elif period == '30':
        start_date = today - timedelta(days=29)
    elif period == '90':
        start_date = today - timedelta(days=89)
    elif period == 'all':
        # Ищем самую раннюю дату среди приёмов пищи и активностей
        earliest_meal = MealRecord.query.order_by(MealRecord.date.asc()).first()
        earliest_activity = ActivityLog.query.order_by(ActivityLog.date.asc()).first()
        earliest_measurement = BodyMeasurement.query.order_by(BodyMeasurement.date.asc()).first()

        min_dates = []
        if earliest_meal:
            min_dates.append(earliest_meal.date)
        if earliest_activity:
            min_dates.append(earliest_activity.date)
        if earliest_measurement:
            min_dates.append(earliest_measurement.date)

        if min_dates:
            start_date = min(min_dates)
        else:
            start_date = today - timedelta(days=30)  # если данных нет
    else:
        start_date = today - timedelta(days=6)

    # Собираем даты от start_date до today (для графика калорий)
    dates_list = []
    current = start_date
    while current <= today:
        dates_list.append(current)
        current += timedelta(days=1)

    labels = [d.strftime('%d.%m') for d in dates_list]

    calorie_intake = []
    calorie_burn = []
    for d in dates_list:
        meals = MealRecord.query.filter(MealRecord.date == d).all()
        activities = ActivityLog.query.filter(ActivityLog.date == d).all()
        intake = sum(meal.total_calories() for meal in meals)
        burn = sum(a.calories_burned for a in activities)
        calorie_intake.append(round(intake, 1))
        calorie_burn.append(round(burn, 1))

    # Замеры тела за выбранный период (или все)
    if period == 'all':
        measurements = BodyMeasurement.query.order_by(BodyMeasurement.date.asc()).all()
    else:
        measurements = BodyMeasurement.query.filter(
            BodyMeasurement.date >= start_date
        ).order_by(BodyMeasurement.date.asc()).all()

    weight_labels = [m.date.strftime('%d.%m') for m in measurements]
    weight_data = [m.weight for m in measurements]

    chest_data = [m.chest if m.chest and m.chest > 0 else None for m in measurements]
    waist_data = [m.waist if m.waist and m.waist > 0 else None for m in measurements]
    hips_data = [m.hips if m.hips and m.hips > 0 else None for m in measurements]
    biceps_data = [m.biceps if m.biceps and m.biceps > 0 else None for m in measurements]

    return render_template('stats.html',
                           labels=labels,
                           calorie_intake=calorie_intake,
                           calorie_burn=calorie_burn,
                           weight_labels=weight_labels,
                           weight_data=weight_data,
                           chest_data=chest_data,
                           waist_data=waist_data,
                           hips_data=hips_data,
                           biceps_data=biceps_data,
                           period=period,
                           today=today)


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