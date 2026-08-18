from database import db
from datetime import datetime


class Product(db.Model):
    """База продуктов (ингредиентов) с КБЖУ на 100г"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    calories = db.Column(db.Float, default=0.0)
    proteins = db.Column(db.Float, default=0.0)
    fats = db.Column(db.Float, default=0.0)
    carbs = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(100), default='')
    image = db.Column(db.String(300), default='')
    default_unit = db.Column(db.String(20), default='г')
    price = db.Column(db.Float, default=0.0)           # Цена
    price_unit = db.Column(db.String(20), default='кг') # ← НОВОЕ: за что цена (кг, шт, л, 100г)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'calories': self.calories,
            'proteins': self.proteins,
            'fats': self.fats,
            'carbs': self.carbs,
            'category': self.category,
            'image': self.image,
            'default_unit': self.default_unit,
            'price': self.price,
            'price_unit': self.price_unit
        }


class Recipe(db.Model):
    """Рецепт блюда"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    image = db.Column(db.String(300), default='')
    prep_time = db.Column(db.Integer, default=0)
    cook_time = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)
    default_portions = db.Column(db.Integer, default=1)
    difficulty = db.Column(db.String(20), default='easy')
    tags = db.Column(db.String(300), default='')
    instructions = db.Column(db.Text, default='')  # JSON steps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    favorites = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)

    ingredients = db.relationship('RecipeIngredient',
                                  backref='recipe',
                                  lazy=True,
                                  cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image': self.image,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'total_time': self.total_time or (self.prep_time + self.cook_time),
            'default_portions': self.default_portions,
            'difficulty': self.difficulty,
            'tags': self.tags,
            'instructions': self.instructions,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'favorites': self.favorites,
            'rating': self.rating,
            'rating_count': self.rating_count
        }


class RecipeIngredient(db.Model):
    """Ингредиент в составе рецепта"""
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', lazy='joined')
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), default='г')

    def to_dict(self):
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'product_calories': self.product.calories if self.product else 0,
            'product_proteins': self.product.proteins if self.product else 0,
            'product_fats': self.product.fats if self.product else 0,
            'product_carbs': self.product.carbs if self.product else 0,
            'quantity': self.quantity,
            'unit': self.unit
        }


class ShoppingItem(db.Model):
    """Элемент списка покупок"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)  # может быть NULL
    name = db.Column(db.String(200), nullable=False)            # название на случай удаления продукта
    quantity = db.Column(db.Float, default=0.0)                 # количество
    unit = db.Column(db.String(20), default='г')                # единица измерения
    purchased = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'quantity': self.quantity,
            'unit': self.unit,
            'purchased': self.purchased
        }

class MealRecord(db.Model):
    """Приём пищи (завтрак, обед и т.д.)"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    meal_type = db.Column(db.String(30), nullable=False, default='завтрак')  # завтрак, обед, ужин, перекус
    time = db.Column(db.Time, nullable=False, default=datetime.utcnow().time())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    entries = db.relationship('MealEntry', backref='meal', lazy=True, cascade="all, delete-orphan")

    def total_calories(self):
        return sum(entry.calories() for entry in self.entries)

    def total_proteins(self):
        return sum(entry.proteins() for entry in self.entries)

    def total_fats(self):
        return sum(entry.fats() for entry in self.entries)

    def total_carbs(self):
        return sum(entry.carbs() for entry in self.entries)


class MealEntry(db.Model):
    """Позиция в приёме пищи (рецепт или продукт)"""
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal_record.id'), nullable=False)

    # Тип позиции: 'recipe' или 'product'
    entry_type = db.Column(db.String(10), nullable=False)

    # ID рецепта или продукта
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)

    # Количество: для рецепта – порции, для продукта – граммы
    quantity = db.Column(db.Float, nullable=False, default=1.0)

    # Связи
    recipe = db.relationship('Recipe', lazy=True)
    product = db.relationship('Product', lazy=True)

    def _recipe_nutrition_per_gram(self):
        """Возвращает КБЖУ на 1 грамм готового блюда"""
        from services.nutrition import calculate_recipe_nutrition
        if not self.recipe:
            return {'calories': 0, 'proteins': 0, 'fats': 0, 'carbs': 0}
        nutrition = calculate_recipe_nutrition(self.recipe, 1)
        total = nutrition['total']
        total_weight = total['weight'] if total['weight'] > 0 else 1
        return {
            'calories': total['calories'] / total_weight,
            'proteins': total['proteins'] / total_weight,
            'fats': total['fats'] / total_weight,
            'carbs': total['carbs'] / total_weight,
        }

    def calories(self):
        if self.entry_type == 'recipe' and self.recipe:
            per_gram = self._recipe_nutrition_per_gram()
            return per_gram['calories'] * self.quantity
        elif self.entry_type == 'product' and self.product:
            return (self.product.calories * self.quantity) / 100
        return 0

    def proteins(self):
        if self.entry_type == 'recipe' and self.recipe:
            per_gram = self._recipe_nutrition_per_gram()
            return per_gram['proteins'] * self.quantity
        elif self.entry_type == 'product' and self.product:
            return (self.product.proteins * self.quantity) / 100
        return 0

    def fats(self):
        if self.entry_type == 'recipe' and self.recipe:
            per_gram = self._recipe_nutrition_per_gram()
            return per_gram['fats'] * self.quantity
        elif self.entry_type == 'product' and self.product:
            return (self.product.fats * self.quantity) / 100
        return 0

    def carbs(self):
        if self.entry_type == 'recipe' and self.recipe:
            per_gram = self._recipe_nutrition_per_gram()
            return per_gram['carbs'] * self.quantity
        elif self.entry_type == 'product' and self.product:
            return (self.product.carbs * self.quantity) / 100
        return 0


class DietGoal(db.Model):
    """Дневные цели по питанию"""
    id = db.Column(db.Integer, primary_key=True)
    calories = db.Column(db.Float, default=2000.0)
    proteins = db.Column(db.Float, default=100.0)
    fats = db.Column(db.Float, default=70.0)
    carbs = db.Column(db.Float, default=250.0)
    goal_type = db.Column(db.String(20), default='maintain')

class UserProfile(db.Model):
    """Профиль пользователя для расчёта калорий"""
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, default=70.0)      # кг
    height = db.Column(db.Float, default=170.0)     # см
    age = db.Column(db.Integer, default=30)
    gender = db.Column(db.String(10), default='male')  # male/female
    activity_level = db.Column(db.String(20), default='medium')  # low/medium/high

    def to_dict(self):
        return {
            'id': self.id,
            'weight': self.weight,
            'height': self.height,
            'age': self.age,
            'gender': self.gender,
            'activity_level': self.activity_level
        }


class ActivityLog(db.Model):
    """Запись о выполненной активности"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    activity_type = db.Column(db.String(100), nullable=False)  # бег, ходьба, плавание и т.д.
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    intensity = db.Column(db.String(20), default='medium')  # low/medium/high
    calories_burned = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'activity_type': self.activity_type,
            'duration_minutes': self.duration_minutes,
            'intensity': self.intensity,
            'calories_burned': self.calories_burned,
            'notes': self.notes
        }

class ActivityGoal(db.Model):
    """Дневные цели по активности"""
    id = db.Column(db.Integer, primary_key=True)
    calories = db.Column(db.Float, default=500.0)            # ккал в день
    duration_minutes = db.Column(db.Integer, default=60)     # минут в день

class ActivityType(db.Model):
    """Пользовательские типы активности с MET-значениями"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    met_low = db.Column(db.Float, default=2.0)
    met_medium = db.Column(db.Float, default=4.0)
    met_high = db.Column(db.Float, default=6.0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'met_low': self.met_low,
            'met_medium': self.met_medium,
            'met_high': self.met_high
        }

class BodyMeasurement(db.Model):
    """Замеры тела пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    weight = db.Column(db.Float, nullable=False, default=0.0)     # кг
    chest = db.Column(db.Float, default=0.0)      # обхват груди, см
    waist = db.Column(db.Float, default=0.0)      # талия, см
    hips = db.Column(db.Float, default=0.0)       # бёдра, см
    biceps = db.Column(db.Float, default=0.0)     # бицепс, см
    notes = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)