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
            'default_unit': self.default_unit
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
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), default='г')
    purchased = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'unit': self.unit,
            'purchased': self.purchased
        }