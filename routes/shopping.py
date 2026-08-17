from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from models import ShoppingItem, Product, Recipe, RecipeIngredient, MealRecord, MealEntry, db
from services.nutrition import calculate_recipe_nutrition
from datetime import datetime, date, timedelta

shopping_bp = Blueprint('shopping', __name__)


@shopping_bp.route('/')
def shopping_list():
    items = ShoppingItem.query.order_by(ShoppingItem.purchased, ShoppingItem.created_at).all()
    return render_template('shopping.html', items=items, today=date.today())


@shopping_bp.route('/add', methods=['POST'])
def add_item():
    """Ручное добавление позиции (с автодополнением)"""
    product_id = request.form.get('product_id', '')
    name = request.form.get('name', '').strip()
    quantity = float(request.form.get('quantity', 0))
    unit = request.form.get('unit', 'г')

    # Если передан product_id, берём название из продукта
    if product_id:
        product = Product.query.get(int(product_id))
        if product:
            name = product.name
            # Если продукт имеет свою единицу по умолчанию и единица не указана, берём её
            if not unit or unit == 'г':
                unit = product.default_unit if product.default_unit else 'г'
    if not name:
        flash('Название продукта обязательно', 'error')
        return redirect(url_for('shopping.shopping_list'))

    item = ShoppingItem(
        product_id=int(product_id) if product_id else None,
        name=name,
        quantity=quantity,
        unit=unit,
        purchased=False
    )
    db.session.add(item)
    db.session.commit()
    flash(f'Добавлено: {name}', 'success')
    return redirect(url_for('shopping.shopping_list'))


@shopping_bp.route('/add-from-recipe/<int:recipe_id>', methods=['POST'])
def add_from_recipe(recipe_id):
    """Добавление всех ингредиентов рецепта в список покупок"""
    recipe = Recipe.query.get_or_404(recipe_id)
    portions = float(request.form.get('portions', 1))

    # Получаем масштабированные ингредиенты
    factor = portions / (recipe.default_portions or 1) if portions != 1 else 1.0

    added = 0
    merged = 0
    for ing in recipe.ingredients:
        product = ing.product
        if not product:
            continue
        new_quantity = ing.quantity * factor
        unit = ing.unit if ing.unit else product.default_unit
        if unit not in ('г', 'мл', 'шт'):
            unit = 'г'

        existing = ShoppingItem.query.filter_by(product_id=product.id, unit=unit, purchased=False).first()
        if existing:
            existing.quantity += new_quantity
            merged += 1
        else:
            item = ShoppingItem(
                product_id=product.id,
                name=product.name,
                quantity=new_quantity,
                unit=unit
            )
            db.session.add(item)
            added += 1

    db.session.commit()
    flash(f'Ингредиенты добавлены: новых позиций {added}, объединено {merged}', 'success')
    return redirect(url_for('shopping.shopping_list'))


@shopping_bp.route('/add-from-diary', methods=['POST'])
def add_from_diary():
    """Добавление продуктов из дневника за период"""
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        end_date = date.today()
        start_date = end_date - timedelta(days=6)

    meals = MealRecord.query.filter(MealRecord.date >= start_date, MealRecord.date <= end_date).all()
    added = 0
    merged = 0

    sum_dict = {}
    for meal in meals:
        for entry in meal.entries:
            if entry.entry_type == 'product' and entry.product:
                product = entry.product
                unit = product.default_unit if product.default_unit else 'г'
                if unit not in ('г', 'мл', 'шт'):
                    unit = 'г'
                key = (product.id, unit)
                if key in sum_dict:
                    sum_dict[key]['quantity'] += entry.quantity
                else:
                    sum_dict[key] = {
                        'product_id': product.id,
                        'name': product.name,
                        'quantity': entry.quantity,
                        'unit': unit
                    }
            elif entry.entry_type == 'recipe' and entry.recipe:
                recipe = entry.recipe
                nutrition = calculate_recipe_nutrition(recipe, 1)
                total_weight = nutrition['total']['weight']
                if total_weight <= 0:
                    continue
                factor = entry.quantity / total_weight
                for ing in recipe.ingredients:
                    product = ing.product
                    if not product:
                        continue
                    needed_qty = ing.quantity * factor
                    unit = ing.unit if ing.unit else product.default_unit
                    if unit not in ('г', 'мл', 'шт'):
                        unit = 'г'
                    key = (product.id, unit)
                    if key in sum_dict:
                        sum_dict[key]['quantity'] += needed_qty
                    else:
                        sum_dict[key] = {
                            'product_id': product.id,
                            'name': product.name,
                            'quantity': needed_qty,
                            'unit': unit
                        }

    for key, data in sum_dict.items():
        existing = ShoppingItem.query.filter_by(product_id=data['product_id'], unit=data['unit'], purchased=False).first()
        if existing:
            existing.quantity += data['quantity']
            merged += 1
        else:
            item = ShoppingItem(
                product_id=data['product_id'],
                name=data['name'],
                quantity=data['quantity'],
                unit=data['unit']
            )
            db.session.add(item)
            added += 1

    db.session.commit()
    flash(f'Собрано из дневника: новых позиций {added}, объединено {merged}', 'success')
    return redirect(url_for('shopping.shopping_list'))


@shopping_bp.route('/toggle/<int:item_id>', methods=['POST'])
def toggle_item(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    item.purchased = not item.purchased
    db.session.commit()
    return jsonify({'status': 'ok', 'purchased': item.purchased})


@shopping_bp.route('/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    item.quantity = float(request.form.get('quantity', item.quantity))
    item.unit = request.form.get('unit', item.unit)
    item.purchased = bool(request.form.get('purchased', item.purchased))
    db.session.commit()
    flash('Позиция обновлена', 'success')
    return redirect(url_for('shopping.shopping_list'))


@shopping_bp.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Позиция удалена', 'success')
    return redirect(url_for('shopping.shopping_list'))


@shopping_bp.route('/clear', methods=['POST'])
def clear_list():
    ShoppingItem.query.delete()
    db.session.commit()
    flash('Список очищен', 'success')
    return redirect(url_for('shopping.shopping_list'))


@shopping_bp.route('/export.txt')
def export_txt():
    items = ShoppingItem.query.order_by(ShoppingItem.purchased, ShoppingItem.name).all()
    lines = ['Список покупок:', '']
    for item in items:
        status = '[x]' if item.purchased else '[ ]'
        lines.append(f'{status} {item.name} — {item.quantity} {item.unit}')
    text = '\n'.join(lines)
    return Response(
        text,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=shopping_list.txt'}
    )