"""
Расчёт калорий, сожжённых при физической активности.
"""
from models import ActivityType  # импорт внутри функций, чтобы избежать циклических зависимостей

MET_VALUES = {
    'бег': {'low': 6.0, 'medium': 9.8, 'high': 12.8},
    'ходьба': {'low': 2.5, 'medium': 3.5, 'high': 4.5},
    'плавание': {'low': 4.5, 'medium': 6.0, 'high': 8.0},
    'велосипед': {'low': 4.0, 'medium': 6.8, 'high': 10.0},
    'силовая тренировка': {'low': 3.5, 'medium': 5.0, 'high': 6.5},
    'йога': {'low': 2.0, 'medium': 3.0, 'high': 4.0},
    'танцы': {'low': 3.0, 'medium': 4.5, 'high': 6.5},
    'аэробика': {'low': 4.0, 'medium': 6.0, 'high': 8.0},
    'другое': {'low': 2.0, 'medium': 4.0, 'high': 6.0},
}


def get_met(activity_type, intensity='medium'):
    """Возвращает MET-значение для активности (сначала ищем в пользовательских типах)"""
    act = activity_type.lower().strip()
    # Проверяем пользовательские типы
    try:
        custom = ActivityType.query.filter_by(name=act).first()
        if custom:
            if intensity == 'low':
                return custom.met_low
            elif intensity == 'high':
                return custom.met_high
            else:
                return custom.met_medium
    except Exception:
        pass  # если нет контекста БД, игнорируем

    # Стандартные типы
    if act in MET_VALUES:
        return MET_VALUES[act].get(intensity, MET_VALUES[act]['medium'])
    return MET_VALUES['другое'].get(intensity, 4.0)


def calculate_calories_burned(weight, activity_type, duration_minutes, intensity='medium'):
    """Рассчитывает сожжённые калории."""
    met = get_met(activity_type, intensity)
    hours = duration_minutes / 60.0
    return round(met * weight * hours, 2)


def get_all_activity_types():
    """Возвращает список всех доступных типов активности (стандартные + пользовательские)."""
    types = []
    # Стандартные
    for name, mets in MET_VALUES.items():
        types.append({
            'name': name,
            'met_low': mets['low'],
            'met_medium': mets['medium'],
            'met_high': mets['high'],
            'is_custom': False
        })
    # Пользовательские
    try:
        customs = ActivityType.query.order_by(ActivityType.name).all()
        for c in customs:
            types.append({
                'name': c.name,
                'met_low': c.met_low,
                'met_medium': c.met_medium,
                'met_high': c.met_high,
                'is_custom': True
            })
    except Exception:
        pass
    return types