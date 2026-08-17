from flask import Blueprint, render_template, request
from models import MealRecord, ActivityLog, BodyMeasurement, UserProfile, DietGoal, db
from datetime import date, timedelta, datetime

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/')
def stats():
    today = date.today()
    period = request.args.get('period', '7')  # 7, 30, 90, all

    # Определяем начальную дату периода
    if period == '7':
        start_date = today - timedelta(days=6)
    elif period == '30':
        start_date = today - timedelta(days=29)
    elif period == '90':
        start_date = today - timedelta(days=89)
    elif period == 'all':
        earliest_meal = MealRecord.query.order_by(MealRecord.date.asc()).first()
        earliest_activity = ActivityLog.query.order_by(ActivityLog.date.asc()).first()
        earliest_measurement = BodyMeasurement.query.order_by(BodyMeasurement.date.asc()).first()

        dates = []
        if earliest_meal: dates.append(earliest_meal.date)
        if earliest_activity: dates.append(earliest_activity.date)
        if earliest_measurement: dates.append(earliest_measurement.date)
        start_date = min(dates) if dates else today - timedelta(days=30)
    else:
        start_date = today - timedelta(days=6)

    # Список дат от start_date до today включительно
    dates_list = []
    current = start_date
    while current <= today:
        dates_list.append(current)
        current += timedelta(days=1)

    # Загружаем профиль и цели
    profile = UserProfile.query.first()
    goal = DietGoal.query.first()
    if not goal:
        goal = DietGoal()  # значения по умолчанию, если нет
        db.session.add(goal)
        db.session.commit()

    # Расчёт TDEE (как в дневнике)
    tdee = None
    if profile and profile.weight > 0 and profile.height > 0 and profile.age > 0:
        if profile.gender == 'male':
            bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
        else:
            bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161
        factors = {'low': 1.2, 'medium': 1.55, 'high': 1.725}
        tdee = bmr * factors.get(profile.activity_level, 1.55)

    total_intake = 0.0
    total_burn = 0.0
    successful_days = 0
    considered_days = 0

    # Списки для графиков
    labels = []
    calorie_intake = []
    calorie_burn = []

    for d in dates_list:
        # Потребление
        meals = MealRecord.query.filter(MealRecord.date == d).all()
        intake = sum(meal.total_calories() for meal in meals)
        # Расход от тренировок
        activities = ActivityLog.query.filter(ActivityLog.date == d).all()
        burned = sum(a.calories_burned for a in activities)

        total_intake += intake
        total_burn += (tdee or 0) + burned  # полный расход = TDEE + тренировки

        # Для графиков
        labels.append(d.strftime('%d.%m'))
        calorie_intake.append(round(intake, 1))
        calorie_burn.append(round(burned, 1))

        # Проверка достижения цели
        if tdee:
            # Рекомендуемое потребление в зависимости от цели
            if goal.goal_type == 'lose':
                recommended = (tdee + burned) - (tdee * 0.2)
            elif goal.goal_type == 'gain':
                recommended = (tdee + burned) + (tdee * 0.1)
            else:
                recommended = tdee + burned

            # Отклонение в пределах ±10% от рекомендуемого
            tolerance = recommended * 0.10
            if abs(intake - recommended) <= tolerance:
                successful_days += 1
            considered_days += 1

    # Средние значения
    days_count = len(dates_list)
    avg_intake = round(total_intake / days_count, 1) if days_count else 0
    avg_burn = round(total_burn / days_count, 1) if days_count else 0
    avg_balance = round(avg_intake - avg_burn, 1)

    achievement_percent = round((successful_days / considered_days) * 100) if considered_days else 0

    # Замеры тела (для графика)
    measurements = BodyMeasurement.query.filter(
        BodyMeasurement.date >= start_date
    ).order_by(BodyMeasurement.date.asc()).all()

    weight_labels = [m.date.strftime('%d.%m') for m in measurements]
    weight_data = [m.weight for m in measurements]
    chest_data = [m.chest if m.chest and m.chest > 0 else None for m in measurements]
    waist_data = [m.waist if m.waist and m.waist > 0 else None for m in measurements]
    hips_data = [m.hips if m.hips and m.hips > 0 else None for m in measurements]
    biceps_data = [m.biceps if m.biceps and m.biceps > 0 else None for m in measurements]

    return render_template(
        'stats.html',
        period=period,
        labels=labels,
        calorie_intake=calorie_intake,
        calorie_burn=calorie_burn,
        avg_intake=avg_intake,
        avg_burn=avg_burn,
        avg_balance=avg_balance,
        achievement_percent=achievement_percent,
        successful_days=successful_days,
        considered_days=considered_days,
        days_count=days_count,
        weight_labels=weight_labels,
        weight_data=weight_data,
        chest_data=chest_data,
        waist_data=waist_data,
        hips_data=hips_data,
        biceps_data=biceps_data,
        today=today
    )