"""
Расчёт КБЖУ и стоимости рецептов.
"""
import math


def get_price_per_100g(product):
    """Пересчитывает цену продукта к 100 г (или 100 мл)"""
    if not product or not product.price or product.price <= 0:
        return 0.0
    unit = product.price_unit or 'кг'
    price = product.price
    if unit == 'кг':
        return round(price / 10, 2)
    elif unit == 'л':
        return round(price / 10, 2)
    elif unit in ('100г', '100мл', 'шт'):
        return price
    elif unit == 'уп':
        return round(price, 2)
    else:
        return round(price / 10, 2)


def get_price_per_unit(product):
    """
    Возвращает цену за единицу измерения продукта.
    """
    if not product or not product.price or product.price <= 0:
        return 0.0, ''

    return product.price, product.price_unit or 'кг'


def calculate_ingredient_cost(product, quantity_grams):
    """
    Рассчитывает стоимость использованного количества продукта.
    Возвращает: (фактическая_стоимость, полная_стоимость_упаковки, нужно_купить, единица_измерения)
    """
    if not product or not product.price or product.price <= 0:
        return 0.0, 0.0, 0, ''

    unit = product.price_unit or 'кг'
    price = product.price

    if unit == 'кг':
        price_per_gram = price / 1000
        actual_cost = price_per_gram * quantity_grams
        kg_needed = math.ceil(quantity_grams / 1000 * 10) / 10
        if kg_needed < 0.1:
            kg_needed = 0.1
        full_cost = kg_needed * price
        return round(actual_cost, 2), round(full_cost, 2), kg_needed, 'кг'

    elif unit == 'л':
        price_per_ml = price / 1000
        actual_cost = price_per_ml * quantity_grams
        l_needed = math.ceil(quantity_grams / 1000 * 10) / 10
        if l_needed < 0.1:
            l_needed = 0.1
        full_cost = l_needed * price
        return round(actual_cost, 2), round(full_cost, 2), l_needed, 'л'

    elif unit == 'шт':
        pieces_needed = max(1, math.ceil(quantity_grams / 50))
        actual_cost = price * (quantity_grams / 50)
        full_cost = price * pieces_needed
        return round(actual_cost, 2), round(full_cost, 2), pieces_needed, 'шт'

    elif unit == '100г':
        price_per_gram = price / 100
        actual_cost = price_per_gram * quantity_grams
        packs_needed = math.ceil(quantity_grams / 100)
        full_cost = packs_needed * price
        return round(actual_cost, 2), round(full_cost, 2), packs_needed, 'уп(100г)'

    elif unit == '100мл':
        price_per_ml = price / 100
        actual_cost = price_per_ml * quantity_grams
        packs_needed = math.ceil(quantity_grams / 100)
        full_cost = packs_needed * price
        return round(actual_cost, 2), round(full_cost, 2), packs_needed, 'уп(100мл)'

    elif unit == 'уп':
        actual_cost = price * (quantity_grams / 100)
        packs_needed = 1
        full_cost = price
        return round(actual_cost, 2), round(full_cost, 2), packs_needed, 'уп'

    else:
        return 0.0, 0.0, 0, ''


def calculate_recipe_nutrition(recipe, portions=None, custom_ingredients=None):
    """
    Рассчитывает КБЖУ и стоимость для рецепта.
    Можно передать custom_ingredients (список временных объектов с product, quantity, unit)
    для расчёта на основе масштабированных ингредиентов.
    """
    if portions is None:
        portions = recipe.default_portions or 1

    source_ingredients = custom_ingredients if custom_ingredients is not None else recipe.ingredients

    total_calories = 0.0
    total_proteins = 0.0
    total_fats = 0.0
    total_carbs = 0.0
    total_weight = 0.0
    total_actual_cost = 0.0
    total_full_cost = 0.0

    ingredients_detail = []
    unpriced = []

    for ingredient in source_ingredients:
        product = ingredient.product
        if not product:
            continue
        factor = ingredient.quantity / 100.0

        total_calories += product.calories * factor
        total_proteins += product.proteins * factor
        total_fats += product.fats * factor
        total_carbs += product.carbs * factor
        total_weight += ingredient.quantity

        actual_cost, full_cost, buy_amount, buy_unit = calculate_ingredient_cost(product, ingredient.quantity)
        total_actual_cost += actual_cost
        total_full_cost += full_cost

        price_per_100g = get_price_per_100g(product)

        if product.price > 0:
            ingredients_detail.append({
                'product_id': product.id,
                'name': product.name,
                'quantity': ingredient.quantity,
                'unit': ingredient.unit if hasattr(ingredient, 'unit') else 'г',
                'price': product.price,
                'price_unit': product.price_unit,
                'actual_cost': actual_cost,
                'full_cost': full_cost,
                'buy_amount': buy_amount,
                'buy_unit': buy_unit,
                'price_per_100g': price_per_100g
            })
        else:
            unpriced.append(product.name)
            ingredients_detail.append({
                'product_id': product.id,
                'name': product.name,
                'quantity': ingredient.quantity,
                'unit': ingredient.unit if hasattr(ingredient, 'unit') else 'г',
                'price': 0,
                'price_unit': '',
                'actual_cost': 0,
                'full_cost': 0,
                'buy_amount': 0,
                'buy_unit': '',
                'price_per_100g': 0.0
            })

    per_portion = {
        'calories': round(total_calories / portions, 1) if portions > 0 else 0,
        'proteins': round(total_proteins / portions, 1) if portions > 0 else 0,
        'fats': round(total_fats / portions, 1) if portions > 0 else 0,
        'carbs': round(total_carbs / portions, 1) if portions > 0 else 0,
        'actual_cost': round(total_actual_cost / portions, 2) if portions > 0 else 0,
        'full_cost': round(total_full_cost / portions, 2) if portions > 0 else 0,
    }

    per_100g = {
        'calories': round((total_calories / total_weight) * 100, 1) if total_weight > 0 else 0,
        'proteins': round((total_proteins / total_weight) * 100, 1) if total_weight > 0 else 0,
        'fats': round((total_fats / total_weight) * 100, 1) if total_weight > 0 else 0,
        'carbs': round((total_carbs / total_weight) * 100, 1) if total_weight > 0 else 0,
        'actual_cost': round((total_actual_cost / total_weight) * 100, 2) if total_weight > 0 else 0,
        'full_cost': round((total_full_cost / total_weight) * 100, 2) if total_weight > 0 else 0,
    }

    return {
        'total': {
            'calories': round(total_calories, 1),
            'proteins': round(total_proteins, 1),
            'fats': round(total_fats, 1),
            'carbs': round(total_carbs, 1),
            'weight': round(total_weight, 1),
        },
        'per_portion': per_portion,
        'per_100g': per_100g,
        'portions': portions,
        'actual_cost': round(total_actual_cost, 2),
        'full_cost': round(total_full_cost, 2),
        'ingredients_detail': ingredients_detail,
        'unpriced': unpriced,
        'priced_count': len([i for i in ingredients_detail if i['price'] > 0]),
    }


def scale_ingredients(recipe, new_portions):
    """Масштабирует ингредиенты пропорционально новому количеству порций."""
    if recipe.default_portions and recipe.default_portions > 0:
        scale_factor = new_portions / recipe.default_portions
        scaled = []
        for ing in recipe.ingredients:
            scaled.append({
                'product': ing.product,
                'quantity': round(ing.quantity * scale_factor, 1),
                'unit': ing.unit
            })
        return scaled
    return recipe.ingredients