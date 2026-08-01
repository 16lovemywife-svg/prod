def calculate_recipe_nutrition(recipe, portions=None):
    """
    Рассчитывает КБЖУ для рецепта.
    Возвращает словарь с данными на весь рецепт, на порцию и на 100г.
    """
    if portions is None:
        portions = recipe.default_portions or 1

    total_calories = 0.0
    total_proteins = 0.0
    total_fats = 0.0
    total_carbs = 0.0
    total_weight = 0.0

    for ingredient in recipe.ingredients:
        if ingredient.product:
            # КБЖУ указаны на 100г продукта
            factor = ingredient.quantity / 100.0
            total_calories += ingredient.product.calories * factor
            total_proteins += ingredient.product.proteins * factor
            total_fats += ingredient.product.fats * factor
            total_carbs += ingredient.product.carbs * factor
            total_weight += ingredient.quantity

    # На порцию
    per_portion = {
        'calories': round(total_calories / portions, 1) if portions > 0 else 0,
        'proteins': round(total_proteins / portions, 1) if portions > 0 else 0,
        'fats': round(total_fats / portions, 1) if portions > 0 else 0,
        'carbs': round(total_carbs / portions, 1) if portions > 0 else 0
    }

    # На 100г готового блюда
    per_100g = {
        'calories': round((total_calories / total_weight) * 100, 1) if total_weight > 0 else 0,
        'proteins': round((total_proteins / total_weight) * 100, 1) if total_weight > 0 else 0,
        'fats': round((total_fats / total_weight) * 100, 1) if total_weight > 0 else 0,
        'carbs': round((total_carbs / total_weight) * 100, 1) if total_weight > 0 else 0
    }

    return {
        'total': {
            'calories': round(total_calories, 1),
            'proteins': round(total_proteins, 1),
            'fats': round(total_fats, 1),
            'carbs': round(total_carbs, 1),
            'weight': round(total_weight, 1)
        },
        'per_portion': per_portion,
        'per_100g': per_100g,
        'portions': portions
    }


def scale_ingredients(recipe, new_portions):
    """Масштабирует ингредиенты пропорционально новому количеству порций"""
    if recipe.default_portions and recipe.default_portions > 0:
        scale_factor = new_portions / recipe.default_portions
        scaled_ingredients = []
        for ingredient in recipe.ingredients:
            scaled_ingredients.append({
                'product': ingredient.product,
                'quantity': round(ingredient.quantity * scale_factor, 1),
                'unit': ingredient.unit
            })
        return scaled_ingredients
    return recipe.ingredients