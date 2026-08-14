from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import ActivityLog, UserProfile, BodyMeasurement, ActivityGoal, ActivityType, db
from services.activity import calculate_calories_burned, get_all_activity_types, MET_VALUES
from datetime import datetime, date, timedelta

workouts_bp = Blueprint('workouts', __name__)


@workouts_bp.route('/')
def workouts():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        workout_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        workout_date = date.today()

    prev_date = workout_date - timedelta(days=1)
    next_date = workout_date + timedelta(days=1)

    activities = ActivityLog.query.filter(ActivityLog.date == workout_date).order_by(ActivityLog.created_at).all()
    user_profile = UserProfile.query.first()
    if not user_profile:
        user_profile = UserProfile()
        db.session.add(user_profile)
        db.session.commit()

    burned_calories = sum(a.calories_burned for a in activities)
    total_duration = sum(a.duration_minutes for a in activities)

    measurement = BodyMeasurement.query.filter(
        BodyMeasurement.date == workout_date
    ).order_by(BodyMeasurement.created_at.desc()).first()

    activity_goal = ActivityGoal.query.first()
    if not activity_goal:
        activity_goal = ActivityGoal()
        db.session.add(activity_goal)
        db.session.commit()

    all_activity_types = get_all_activity_types()
    custom_activity_types = ActivityType.query.order_by(ActivityType.name).all()

    return render_template('workouts.html',
                           date=workout_date,
                           prev_date=prev_date,
                           next_date=next_date,
                           activities=activities,
                           profile=user_profile,
                           burned_calories=burned_calories,
                           total_duration=total_duration,
                           measurement=measurement,
                           activity_goal=activity_goal,
                           all_activity_types=all_activity_types,
                           custom_activity_types=custom_activity_types,
                           today=date.today())


@workouts_bp.route('/add', methods=['POST'])
def add_activity():
    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    activity_type = request.form.get('activity_type', 'другое')
    duration_minutes = int(request.form.get('duration_minutes', 30))
    intensity = request.form.get('intensity', 'medium')
    weight = float(request.form.get('weight', 70))

    calories_input = request.form.get('calories_burned', '')
    if calories_input.strip():
        calories = float(calories_input)
    else:
        calories = calculate_calories_burned(weight, activity_type, duration_minutes, intensity)

    try:
        workout_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        workout_date = date.today()

    activity = ActivityLog(
        date=workout_date,
        activity_type=activity_type,
        duration_minutes=duration_minutes,
        intensity=intensity,
        calories_burned=calories,
        notes=request.form.get('notes', '')
    )
    db.session.add(activity)
    db.session.commit()
    flash('Активность добавлена!', 'success')
    return redirect(url_for('workouts.workouts', date=date_str))


@workouts_bp.route('/edit/<int:activity_id>', methods=['POST'])
def edit_activity(activity_id):
    activity = ActivityLog.query.get_or_404(activity_id)
    activity.activity_type = request.form.get('activity_type', activity.activity_type)
    activity.duration_minutes = int(request.form.get('duration_minutes', activity.duration_minutes))
    activity.intensity = request.form.get('intensity', activity.intensity)

    calories_input = request.form.get('calories_burned', '')
    if calories_input.strip():
        activity.calories_burned = float(calories_input)
    else:
        weight = float(request.form.get('weight', 70))
        activity.calories_burned = calculate_calories_burned(weight, activity.activity_type, activity.duration_minutes, activity.intensity)

    activity.notes = request.form.get('notes', '')
    db.session.commit()
    flash('Активность обновлена', 'success')
    return redirect(url_for('workouts.workouts', date=activity.date.strftime('%Y-%m-%d')))


@workouts_bp.route('/delete/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    activity = ActivityLog.query.get_or_404(activity_id)
    activity_date = activity.date
    db.session.delete(activity)
    db.session.commit()
    flash('Активность удалена', 'success')
    return redirect(url_for('workouts.workouts', date=activity_date.strftime('%Y-%m-%d')))


@workouts_bp.route('/add-measurement', methods=['POST'])
def add_measurement():
    date_str = request.form.get('date')
    try:
        measurement_date = datetime.strptime(date_str, '%Y-%m-%d').date()
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
    return redirect(url_for('workouts.workouts', date=measurement_date.strftime('%Y-%m-%d')))


@workouts_bp.route('/delete-measurement/<int:measurement_id>', methods=['POST'])
def delete_measurement(measurement_id):
    measurement = BodyMeasurement.query.get_or_404(measurement_id)
    measurement_date = measurement.date
    db.session.delete(measurement)
    db.session.commit()
    flash('Замер удалён', 'success')
    return redirect(url_for('workouts.workouts', date=measurement_date.strftime('%Y-%m-%d')))


@workouts_bp.route('/update-goal', methods=['POST'])
def update_goal():
    goal = ActivityGoal.query.first()
    if not goal:
        goal = ActivityGoal()
        db.session.add(goal)

    goal.calories = float(request.form.get('calories', goal.calories))
    goal.duration_minutes = int(request.form.get('duration_minutes', goal.duration_minutes))
    db.session.commit()
    flash('Цели обновлены!', 'success')
    return redirect(url_for('workouts.workouts'))


@workouts_bp.route('/add-activity-type', methods=['POST'])
def add_activity_type():
    name = request.form.get('name', '').strip().lower()
    if not name:
        flash('Название обязательно', 'error')
        return redirect(url_for('workouts.workouts'))

    if name in MET_VALUES:
        flash('Такой тип уже существует', 'error')
        return redirect(url_for('workouts.workouts'))

    if ActivityType.query.filter_by(name=name).first():
        flash('Такой тип уже существует', 'error')
        return redirect(url_for('workouts.workouts'))

    activity_type = ActivityType(
        name=name,
        met_low=float(request.form.get('met_low', 2.0)),
        met_medium=float(request.form.get('met_medium', 4.0)),
        met_high=float(request.form.get('met_high', 6.0))
    )
    db.session.add(activity_type)
    db.session.commit()
    flash('Тип активности добавлен!', 'success')
    return redirect(url_for('workouts.workouts'))


@workouts_bp.route('/delete-activity-type/<int:type_id>', methods=['POST'])
def delete_activity_type(type_id):
    activity_type = ActivityType.query.get_or_404(type_id)
    db.session.delete(activity_type)
    db.session.commit()
    flash('Тип активности удалён', 'success')
    return redirect(url_for('workouts.workouts'))