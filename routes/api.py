from flask import Blueprint, request, jsonify
from models import Recipe, RecipeIngredient, Product, db
from services.nutrition import calculate_recipe_nutrition

api_bp = Blueprint('api', __name__)


@api_bp.route('/calculate-nutrition/<int:recipe_id>', methods=['POST'])
def calculate_nutrition_api(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json() or {}
    portions = data.get('portions', recipe.default_portions)

    custom_ingredients = None
    if 'ingredients' in data:
        custom_ingredients = []
        for ing_data in data['ingredients']:
            product = Product.query.get(ing_data['product_id'])
            if product:
                temp_ing = type('TempIngredient', (), {
                    'product': product,
                    'quantity': float(ing_data.get('quantity', 0)),
                    'unit': ing_data.get('unit', 'г')
                })()
                custom_ingredients.append(temp_ing)

    nutrition = calculate_recipe_nutrition(recipe, portions, custom_ingredients)
    return jsonify(nutrition)


@api_bp.route('/search-products')
def search_products():
    """Поиск продуктов для автодополнения"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    products = Product.query.filter(
        Product.name.ilike(f'%{query}%')
    ).limit(10).all()

    return jsonify([p.to_dict() for p in products])


@api_bp.route('/replace-ingredient/<int:recipe_id>', methods=['POST'])
def replace_ingredient(recipe_id):
    """Замена ингредиента в рецепте (без сохранения)"""
    data = request.get_json()
    old_product_id = data.get('old_product_id')
    new_product_id = data.get('new_product_id')
    quantity = data.get('quantity', 0)
    unit = data.get('unit', 'г')

    if not all([old_product_id, new_product_id]):
        return jsonify({'status': 'error', 'message': 'Не указаны продукты'}), 400

    old_product = Product.query.get(old_product_id)
    new_product = Product.query.get(new_product_id)

    if not old_product or not new_product:
        return jsonify({'status': 'error', 'message': 'Продукт не найден'}), 404

    # Возвращаем информацию о новом продукте и пересчитанное КБЖУ
    factor = quantity / 100.0
    return jsonify({
        'status': 'ok',
        'new_ingredient': {
            'product_id': new_product.id,
            'product_name': new_product.name,
            'quantity': quantity,
            'unit': unit,
            'calories': round(new_product.calories * factor, 1),
            'proteins': round(new_product.proteins * factor, 1),
            'fats': round(new_product.fats * factor, 1),
            'carbs': round(new_product.carbs * factor, 1)
        }
    })


@api_bp.route('/recipes/by-ingredients')
def find_by_ingredients():
    """Поиск рецептов по имеющимся ингредиентам (режим Холодильник)"""
    product_ids = request.args.getlist('product_ids[]')
    if not product_ids:
        return jsonify([])

    # Ищем рецепты, содержащие хотя бы один из указанных продуктов
    from sqlalchemy import and_
    recipe_ids = RecipeIngredient.query.filter(
        RecipeIngredient.product_id.in_([int(pid) for pid in product_ids])
    ).with_entities(RecipeIngredient.recipe_id).distinct().all()

    recipe_ids = [r[0] for r in recipe_ids]
    recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).limit(20).all()

    return jsonify([r.to_dict() for r in recipes])