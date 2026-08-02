import json
import os
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, jsonify)
from werkzeug.utils import secure_filename
from models import Recipe, RecipeIngredient, Product, db
from services.nutrition import calculate_recipe_nutrition

recipes_bp = Blueprint('recipes', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'png', 'jpg', 'jpeg', 'gif', 'webp'
    }


def save_uploaded_file(file):
    """Сохраняет загруженный файл и возвращает путь к нему"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Добавляем префикс для уникальности
        import time
        filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return 'uploads/' + filename
    return ''


@recipes_bp.route('/')
def recipe_list():
    """Список всех рецептов (редирект на главную с фильтром)"""
    return redirect(url_for('main.index'))


@recipes_bp.route('/add', methods=['GET', 'POST'])
def add_recipe():
    """Добавление нового рецепта"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Название рецепта обязательно', 'error')
            return redirect(url_for('recipes.add_recipe'))

        # Создаём рецепт
        recipe = Recipe()
        recipe.title = title
        recipe.description = request.form.get('description', '')
        recipe.prep_time = int(request.form.get('prep_time', 0))
        recipe.cook_time = int(request.form.get('cook_time', 0))
        recipe.total_time = recipe.prep_time + recipe.cook_time
        recipe.default_portions = int(request.form.get('default_portions', 1))
        recipe.difficulty = request.form.get('difficulty', 'easy')
        recipe.tags = request.form.get('tags', '')

        # Обработка фото
        image_file = request.files.get('image')
        if image_file:
            recipe.image = save_uploaded_file(image_file)

        # Инструкция (шаги) - сохраняем как JSON
        steps = []
        step_texts = request.form.getlist('step_text[]')
        step_times = request.form.getlist('step_time[]')
        for i, text in enumerate(step_texts):
            if text.strip():
                step = {
                    'step_number': i + 1,
                    'instruction': text.strip(),
                    'timer_minutes': int(step_times[i]) if i < len(
                        step_times) and step_times[i] else 0
                }
                steps.append(step)
        recipe.instructions = json.dumps(steps, ensure_ascii=False)

        db.session.add(recipe)
        db.session.flush()  # Получаем recipe.id

        # Добавляем ингредиенты
        product_ids = request.form.getlist('ingredient_product[]')
        quantities = request.form.getlist('ingredient_quantity[]')
        units = request.form.getlist('ingredient_unit[]')

        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i]:
                ingredient = RecipeIngredient()
                ingredient.recipe_id = recipe.id
                ingredient.product_id = int(product_ids[i])
                ingredient.quantity = float(quantities[i])
                ingredient.unit = units[i] if i < len(units) else 'г'
                db.session.add(ingredient)

        db.session.commit()
        flash('Рецепт успешно добавлен!', 'success')
        return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))

    # GET запрос - показываем форму
    products = Product.query.order_by(Product.name).all()
    return render_template('recipe_form.html',
                           recipe=None,
                           products=products,
                           is_edit=False)


@recipes_bp.route('/<int:recipe_id>')
def view_recipe(recipe_id):
    """Просмотр рецепта с расчётом КБЖУ и стоимости"""
    recipe = Recipe.query.get_or_404(recipe_id)
    nutrition = calculate_recipe_nutrition(recipe)

    # Парсим инструкции из JSON
    steps = []
    if recipe.instructions:
        try:
            steps = json.loads(recipe.instructions)
        except (json.JSONDecodeError, TypeError):
            steps = [{'step_number': 1, 'instruction': recipe.instructions, 'timer_minutes': 0}]

    # Похожие рецепты
    similar_recipes = []
    if recipe.tags:
        tags = [t.strip() for t in recipe.tags.split(',') if t.strip()]
        if tags:
            similar_recipes = Recipe.query.filter(
                Recipe.id != recipe.id,
                Recipe.tags.ilike(f'%{tags[0]}%')
            ).limit(4).all()

    return render_template(
        'recipe_detail.html',
        recipe=recipe,
        nutrition=nutrition,
        steps=steps,
        similar_recipes=similar_recipes
    )


@recipes_bp.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Редактирование рецепта"""
    recipe = Recipe.query.get_or_404(recipe_id)

    if request.method == 'POST':
        recipe.title = request.form.get('title', '').strip()
        recipe.description = request.form.get('description', '')
        recipe.prep_time = int(request.form.get('prep_time', 0))
        recipe.cook_time = int(request.form.get('cook_time', 0))
        recipe.total_time = recipe.prep_time + recipe.cook_time
        recipe.default_portions = int(request.form.get('default_portions', 1))
        recipe.difficulty = request.form.get('difficulty', 'easy')
        recipe.tags = request.form.get('tags', '')

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            recipe.image = save_uploaded_file(image_file)

        # Собираем шаги из формы
        steps = []
        step_texts = request.form.getlist('step_text[]')
        step_times = request.form.getlist('step_time[]')

        for i, text in enumerate(step_texts):
            text = text.strip()
            if text:  # Только непустые шаги
                timer = 0
                if i < len(step_times) and step_times[i]:
                    try:
                        timer = int(step_times[i])
                    except ValueError:
                        timer = 0
                steps.append({
                    'step_number': i + 1,
                    'instruction': text,
                    'timer_minutes': timer
                })

        # ВАЖНО: обновляем инструкции ТОЛЬКО если шаги не пустые
        if steps:
            recipe.instructions = json.dumps(steps, ensure_ascii=False)

        # Обновляем ингредиенты
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        product_ids = request.form.getlist('ingredient_product[]')
        quantities = request.form.getlist('ingredient_quantity[]')
        units = request.form.getlist('ingredient_unit[]')

        for i in range(len(product_ids)):
            if product_ids[i] and quantities[i]:
                ingredient = RecipeIngredient()
                ingredient.recipe_id = recipe.id
                ingredient.product_id = int(product_ids[i])
                ingredient.quantity = float(quantities[i])
                ingredient.unit = units[i] if i < len(units) else 'г'
                db.session.add(ingredient)

        db.session.commit()
        flash('Рецепт обновлён!', 'success')
        return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))

    # GET — готовим данные для формы
    products = Product.query.order_by(Product.name).all()

    # Парсим существующие шаги из JSON
    existing_steps = []
    if recipe.instructions:
        try:
            existing_steps = json.loads(recipe.instructions)
        except (json.JSONDecodeError, TypeError):
            existing_steps = []

    return render_template('recipe_form.html',
                           recipe=recipe,
                           products=products,
                           is_edit=True,
                           existing_steps=existing_steps)


@recipes_bp.route('/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    """Удаление рецепта"""
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash('Рецепт удалён', 'success')
    return redirect(url_for('main.index'))


@recipes_bp.route('/<int:recipe_id>/cooking-mode')
def cooking_mode(recipe_id):
    """Режим готовки - полноэкранный"""
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = []
    if recipe.instructions:
        try:
            steps = json.loads(recipe.instructions)
        except json.JSONDecodeError:
            steps = [{'step_number': 1, 'instruction': recipe.instructions,
                      'timer_minutes': 0}]
    return render_template('cooking_mode.html', recipe=recipe, steps=steps)


@recipes_bp.route('/<int:recipe_id>/toggle-favorite', methods=['POST'])
def toggle_favorite(recipe_id):
    """Добавление/удаление из избранного"""
    recipe = Recipe.query.get_or_404(recipe_id)
    recipe.favorites = not recipe.favorites
    db.session.commit()
    return jsonify({'status': 'ok', 'is_favorite': recipe.favorites})


@recipes_bp.route('/<int:recipe_id>/rate', methods=['POST'])
def rate_recipe(recipe_id):
    """Оценка рецепта"""
    recipe = Recipe.query.get_or_404(recipe_id)
    data = request.get_json()
    score = int(data.get('score', 0))

    if score < 1 or score > 5:
        return jsonify({'status': 'error', 'message': 'Оценка от 1 до 5'}), 400

    # Обновляем средний рейтинг
    total_score = recipe.rating * recipe.rating_count + score
    recipe.rating_count += 1
    recipe.rating = round(total_score / recipe.rating_count, 1)

    db.session.commit()
    return jsonify({
        'status': 'ok',
        'rating': recipe.rating,
        'rating_count': recipe.rating_count
    })