"""
Расчёт калорий, сожжённых при физической активности.
"""

# Справочник MET-значений для разных типов активности
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
    """Возвращает MET-значение для активности и интенсивности."""
    act = activity_type.lower().strip()
    if act in MET_VALUES:
        return MET_VALUES[act].get(intensity, MET_VALUES[act]['medium'])
    return MET_VALUES['другое'].get(intensity, 4.0)


def calculate_calories_burned(weight, activity_type, duration_minutes, intensity='medium'):
    """
    Рассчитывает сожжённые калории.
    Формула: калории = MET * вес (кг) * время (часы)
    """
    met = get_met(activity_type, intensity)
    hours = duration_minutes / 60.0
    return round(met * weight * hours, 2)