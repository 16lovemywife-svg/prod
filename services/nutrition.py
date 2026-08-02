"""
Расчёт КБЖУ и стоимости рецептов.
"""
import math


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
        # Цена за 1 кг (1000 г)
        price_per_gram = price / 1000
        actual_cost = price_per_gram * quantity_grams

        # Сколько кг нужно купить (округляем вверх)
        kg_needed = math.ceil(quantity_grams / 1000 * 10) / 10  # с точностью до 100г
        if kg_needed < 0.1:
            kg_needed = 0.1  # минимум 100г
        full_cost = kg_needed * price

        return round(actual_cost, 2), round(full_cost, 2), kg_needed, 'кг'

    elif unit == 'л':
        # Цена за 1 литр (1000 мл)
        price_per_ml = price / 1000
        actual_cost = price_per_ml * quantity_grams  # для жидкостей г ≈ мл

        # Сколько литров нужно купить
        l_needed = math.ceil(quantity_grams / 1000 * 10) / 10
        if l_needed < 0.1:
            l_needed = 0.1
        full_cost = l_needed * price

        return round(actual_cost, 2), round(full_cost, 2), l_needed, 'л'

    elif unit == 'шт':
        # Цена за штуку
        # quantity_grams для яиц — это количество в граммах
        # 1 яйцо ≈ 50г, так что переводим в штуки
        pieces_needed = max(1, math.ceil(quantity_grams / 50))
        actual_cost = price * (quantity_grams / 50)  # пропорционально весу
        full_cost = price * pieces_needed

        return round(actual_cost, 2), round(full_cost, 2), pieces_needed, 'шт'

    elif unit == '100г':
        # Цена за 100 г
        price_per_gram = price / 100
        actual_cost = price_per_gram * quantity_grams

        # Сколько упаковок по 100г нужно
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
        # Цена за упаковку
        actual_cost = price * (quantity_grams / 100)  # примерный расчёт
        packs_needed = 1
        full_cost = price

        return round(actual_cost, 2), round(full_cost, 2), packs_needed, 'уп'

    else:
        return 0.0, 0.0, 0, ''


def calculate_recipe_nutrition(recipe, portions=None):
    """
    Рассчитывает КБЖУ и стоимость для рецепта.

    Возвращает:
    {
        'total': {...},
        'per_portion': {...},
        'per_100g': {...},
        'full_cost': float,      # Полная стоимость (покупка целых упаковок)
        'actual_cost': float,    # Фактическая стоимость (только использованное)
        'ingredients_detail': [...]  # Детализация по каждому ингредиенту
    }
    """
    if portions is None:
        portions = recipe.default_portions or 1

    total_calories = 0.0
    total_proteins = 0.0
    total_fats = 0.0
    total_carbs = 0.0
    total_weight = 0.0
    total_actual_cost = 0.0
    total_full_cost = 0.0

    ingredients_detail = []
    unpriced = []

    for ingredient in recipe.ingredients:
        if ingredient.product:
            factor = ingredient.quantity / 100.0

            # КБЖУ
            total_calories += ingredient.product.calories * factor
            total_proteins += ingredient.product.proteins * factor
            total_fats += ingredient.product.fats * factor
            total_carbs += ingredient.product.carbs * factor
            total_weight += ingredient.quantity

            # Стоимость
            actual_cost, full_cost, buy_amount, buy_unit = calculate_ingredient_cost(
                ingredient.product, ingredient.quantity
            )

            total_actual_cost += actual_cost
            total_full_cost += full_cost

            if ingredient.product.price > 0:
                ingredients_detail.append({
                    'name': ingredient.product.name,
                    'quantity': ingredient.quantity,
                    'unit': ingredient.unit,
                    'price': ingredient.product.price,
                    'price_unit': ingredient.product.price_unit,
                    'actual_cost': actual_cost,
                    'full_cost': full_cost,
                    'buy_amount': buy_amount,
                    'buy_unit': buy_unit
                })
            else:
                unpriced.append(ingredient.product.name)
                ingredients_detail.append({
                    'name': ingredient.product.name,
                    'quantity': ingredient.quantity,
                    'unit': ingredient.unit,
                    'price': 0,
                    'price_unit': '',
                    'actual_cost': 0,
                    'full_cost': 0,
                    'buy_amount': 0,
                    'buy_unit': ''
                })

    return {
        'total': {
            'calories': round(total_calories, 1),
            'proteins': round(total_proteins, 1),
            'fats': round(total_fats, 1),
            'carbs': round(total_carbs, 1),
            'weight': round(total_weight, 1),
        },
        'per_portion': {
            'calories': round(total_calories / portions, 1) if portions > 0 else 0,
            'proteins': round(total_proteins / portions, 1) if portions > 0 else 0,
            'fats': round(total_fats / portions, 1) if portions > 0 else 0,
            'carbs': round(total_carbs / portions, 1) if portions > 0 else 0,
            'actual_cost': round(total_actual_cost / portions, 2) if portions > 0 else 0,
            'full_cost': round(total_full_cost / portions, 2) if portions > 0 else 0,
        },
        'per_100g': {
            'calories': round((total_calories / total_weight) * 100, 1) if total_weight > 0 else 0,
            'proteins': round((total_proteins / total_weight) * 100, 1) if total_weight > 0 else 0,
            'fats': round((total_fats / total_weight) * 100, 1) if total_weight > 0 else 0,
            'carbs': round((total_carbs / total_weight) * 100, 1) if total_weight > 0 else 0,
            'actual_cost': round((total_actual_cost / total_weight) * 100, 2) if total_weight > 0 else 0,
            'full_cost': round((total_full_cost / total_weight) * 100, 2) if total_weight > 0 else 0,
        },
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