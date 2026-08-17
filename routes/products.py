import os
import time
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app)
from werkzeug.utils import secure_filename
from models import Product, RecipeIngredient, db
from sqlalchemy import func

products_bp = Blueprint('products', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'png', 'jpg', 'jpeg', 'gif', 'webp'
    }


def save_product_image(file):
    """Сохраняет изображение продукта"""
    if file and allowed_file(file.filename):
        filename = f"product_{int(time.time())}_{secure_filename(file.filename)}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return 'uploads/' + filename
    return ''


def get_price_per_100g(product):
    """Пересчитывает цену к 100г для расчётов в рецептах"""
    if not product.price or product.price <= 0:
        return 0.0

    unit = product.price_unit or 'кг'
    price = product.price

    if unit == 'кг':
        return price / 10
    elif unit == 'л':
        return price / 10
    elif unit == '100г':
        return price
    elif unit == '100мл':
        return price
    elif unit == 'шт':
        return price
    elif unit == 'уп':
        return price
    else:
        return price / 10


def format_price(product):
    """Форматирует цену для отображения"""
    if not product.price or product.price <= 0:
        return "—"

    unit = product.price_unit or 'кг'
    price = product.price

    units_display = {
        'кг': f'{price:.2f} ₽/кг',
        'л': f'{price:.2f} ₽/л',
        'шт': f'{price:.2f} ₽/шт',
        '100г': f'{price:.2f} ₽/100г',
        '100мл': f'{price:.2f} ₽/100мл',
        'уп': f'{price:.2f} ₽/уп',
    }

    return units_display.get(unit, f'{price:.2f} ₽/{unit}')


@products_bp.route('/')
def product_list():
    """Список всех продуктов"""
    search_query = request.args.get('q', '')
    category_filter = request.args.get('category', '')

    query = Product.query

    if search_query:
        query = query.filter(func.lower(Product.name).contains(search_query.lower()))

    if category_filter:
        query = query.filter(Product.category == category_filter)

    products = query.order_by(Product.name).all()

    # Все категории для фильтра
    categories = [row[0] for row in
                  Product.query.with_entities(Product.category).distinct().all()
                  if row[0]]

    return render_template('products.html',
                           products=products,
                           query=search_query,
                           categories=sorted(categories),
                           category_filter=category_filter,
                           format_price=format_price)


@products_bp.route('/add', methods=['GET', 'POST'])
def add_product():
    """Добавление нового продукта"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Название продукта обязательно', 'error')
            return redirect(url_for('products.add_product'))

        existing = Product.query.filter(Product.name.ilike(name)).first()
        if existing:
            flash(f'Продукт "{name}" уже существует', 'error')
            return redirect(url_for('products.add_product'))

        product = Product()
        product.name = name
        product.calories = float(request.form.get('calories', 0))
        product.proteins = float(request.form.get('proteins', 0))
        product.fats = float(request.form.get('fats', 0))
        product.carbs = float(request.form.get('carbs', 0))
        product.category = request.form.get('category', '')
        product.default_unit = request.form.get('default_unit', 'г')

        # Цена и единица измерения
        price_str = request.form.get('price', '0')
        product.price = float(price_str) if price_str else 0.0
        product.price_unit = request.form.get('price_unit', 'кг')

        image_file = request.files.get('image')
        if image_file:
            product.image = save_product_image(image_file)

        db.session.add(product)
        db.session.commit()

        if product.price > 0:
            flash(f'Продукт "{name}" добавлен! ({format_price(product)})', 'success')
        else:
            flash(f'Продукт "{name}" добавлен!', 'success')

        return redirect(url_for('products.product_list'))

    return render_template('product_form.html', product=None, is_edit=False)


@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    """Редактирование продукта"""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.calories = float(request.form.get('calories', 0))
        product.proteins = float(request.form.get('proteins', 0))
        product.fats = float(request.form.get('fats', 0))
        product.carbs = float(request.form.get('carbs', 0))
        product.category = request.form.get('category', '')
        product.default_unit = request.form.get('default_unit', 'г')

        # Обновляем цену
        price_str = request.form.get('price', '0')
        product.price = float(price_str) if price_str else 0.0
        product.price_unit = request.form.get('price_unit', 'кг')

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            product.image = save_product_image(image_file)

        db.session.commit()
        flash('Продукт обновлён!', 'success')
        return redirect(url_for('products.product_list'))

    return render_template('product_form.html', product=product, is_edit=True)


@products_bp.route('/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Удаление продукта"""
    product = Product.query.get_or_404(product_id)

    # Проверяем использование в рецептах
    usage_count = RecipeIngredient.query.filter_by(product_id=product_id).count()
    if usage_count > 0:
        flash(f'Нельзя удалить: продукт используется в {usage_count} рецептах', 'error')
        return redirect(url_for('products.product_list'))

    db.session.delete(product)
    db.session.commit()
    flash('Продукт удалён', 'success')
    return redirect(url_for('products.product_list'))