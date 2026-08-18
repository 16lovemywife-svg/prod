from flask import Blueprint, request, jsonify
from models import Recipe, RecipeIngredient, Product, db
from services.nutrition import calculate_recipe_nutrition
from sqlalchemy import func

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
    query = request.args.get('q', '').strip().lower()
    if query:
        all_products = Product.query.all()
        products = [p for p in all_products if query in p.name.lower()][:20]
    else:
        products = Product.query.order_by(Product.name).limit(20).all()
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
    product_ids = request.args.getlist('product_ids[]')
    require_all = request.args.get('require_all', '0') == '1'

    if not product_ids:
        return jsonify([])

    try:
        ids = [int(pid) for pid in product_ids]
    except ValueError:
        return jsonify([])

    # Получаем ID рецептов, содержащих хотя бы один из выбранных продуктов
    recipe_ids = RecipeIngredient.query.filter(
        RecipeIngredient.product_id.in_(ids)
    ).with_entities(RecipeIngredient.recipe_id).distinct().all()
    recipe_ids = [r[0] for r in recipe_ids]

    if not recipe_ids:
        return jsonify([])

    recipes = Recipe.query.filter(Recipe.id.in_(recipe_ids)).all()

    result = []
    for recipe in recipes:
        ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
        total_ingredients = len(ingredients)
        matched_ingredients = sum(1 for ing in ingredients if ing.product_id in ids)

        # Если включён фильтр "только полные совпадения" и рецепт не подходит, пропускаем
        if require_all and matched_ingredients < total_ingredients:
            continue

        missing_ingredients = [ing.product.name for ing in ingredients if ing.product_id not in ids]
        match_percent = round((matched_ingredients / total_ingredients) * 100) if total_ingredients > 0 else 0

        data = recipe.to_dict()
        data['missing_ingredients'] = missing_ingredients
        data['match_percent'] = match_percent
        data['matched_count'] = matched_ingredients
        data['total_ingredients'] = total_ingredients
        result.append(data)

    # Сортировка: сначала по проценту совпадения, затем по количеству совпавших, затем по названию
    result.sort(key=lambda x: (-x['match_percent'], -x['matched_count'], x['title'].lower()))

    return jsonify(result)


@api_bp.route('/search-recipes')
def search_recipes():
    query = request.args.get('q', '').strip().lower()
    if query:
        all_recipes = Recipe.query.all()
        recipes = [r for r in all_recipes if query in r.title.lower()][:20]
    else:
        recipes = Recipe.query.order_by(Recipe.title).limit(20).all()
    return jsonify([{'id': r.id, 'title': r.title} for r in recipes])