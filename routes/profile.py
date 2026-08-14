from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import UserProfile, db

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/', methods=['GET', 'POST'])
def profile():
    """Просмотр и сохранение профиля пользователя"""
    user_profile = UserProfile.query.first()
    if not user_profile:
        user_profile = UserProfile()
        db.session.add(user_profile)
        db.session.commit()

    if request.method == 'POST':
        user_profile.weight = float(request.form.get('weight', user_profile.weight))
        user_profile.height = float(request.form.get('height', user_profile.height))
        user_profile.age = int(request.form.get('age', user_profile.age))
        user_profile.gender = request.form.get('gender', user_profile.gender)
        user_profile.activity_level = request.form.get('activity_level', user_profile.activity_level)
        db.session.commit()
        flash('Профиль сохранён', 'success')
        return redirect(url_for('profile.profile'))

    return render_template('profile.html', profile=user_profile)