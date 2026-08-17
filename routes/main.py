from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Recipe, Product, RecipeIngredient
from sqlalchemy import or_, func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Главная страница с поиском, фильтрами и пагинацией"""
    search_query = request.args.get('q', '')
    difficulty_filter = request.args.get('difficulty', '')
    favorites_filter = request.args.get('favorites', '0')
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Базовый запрос
    query = Recipe.query

    # Поиск
    if search_query:
        search_lower = search_query.lower()
        all_recipes = Recipe.query.all()
        filtered = []
        for r in all_recipes:
            if (search_lower in r.title.lower() or
                    search_lower in (r.description or '').lower() or
                    search_lower in (r.tags or '').lower() or
                    any(search_lower in (ing.product.name.lower() if ing.product else '') for ing in r.ingredients)):
                filtered.append(r)
        # Применяем сортировку
        if sort_by == 'quick':
            filtered.sort(key=lambda x: x.total_time)
        else:
            filtered.sort(key=lambda x: x.created_at, reverse=True)
        # Пагинация вручную
        total = len(filtered)
        per_page = 12
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * per_page
        end = start + per_page
        recipes = filtered[start:end]

        class Pagination:
            pass

        pagination = Pagination()
        pagination.page = page
        pagination.per_page = per_page
        pagination.total = total
        pagination.pages = (total // per_page) + (1 if total % per_page else 0)
        pagination.has_prev = page > 1
        pagination.has_next = end < total
        pagination.prev_num = page - 1
        pagination.next_num = page + 1
    else:
        # обычная пагинация
        query = Recipe.query

    # Фильтр по сложности
    if difficulty_filter:
        query = query.filter(Recipe.difficulty == difficulty_filter)

    # Фильтр по избранному
    if favorites_filter == '1':
        query = query.filter(Recipe.favorites == True)

    # Сортировка
    if sort_by == 'quick':
        query = query.order_by(Recipe.total_time.asc())
    else:  # newest
        query = query.order_by(Recipe.created_at.desc())

    # Пагинация
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    recipes = pagination.items

    # Категории для hero-блока
    categories = [
        {'name': 'Завтраки', 'icon': '🌅', 'tag': 'завтрак'},
        {'name': 'Салаты', 'icon': '🥗', 'tag': 'салат'},
        {'name': 'Супы', 'icon': '🍲', 'tag': 'суп'},
        {'name': 'Горячее', 'icon': '🍖', 'tag': 'горячее'},
        {'name': 'Десерты', 'icon': '🍰', 'tag': 'десерт'},
        {'name': 'Напитки', 'icon': '🍹', 'tag': 'напиток'},
    ]

    # Статистика
    stats = {
        'total_recipes': Recipe.query.count(),
        'total_products': Product.query.count(),
    }

    return render_template(
        'index.html',
        recipes=recipes,
        query=search_query,
        categories=categories,
        stats=stats,
        difficulty_filter=difficulty_filter,
        favorites_filter=favorites_filter,
        sort_by=sort_by,
        pagination=pagination
    )


@main_bp.route('/search')
def search():
    """Расширенный поиск по рецептам и продуктам с отдельной страницей"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, recipes, products
    page = request.args.get('page', 1, type=int)
    per_page = 20

    recipes = []
    products = []
    total_recipes = 0
    total_products = 0

    if query:
        if search_type in ('all', 'recipes'):
            all_recipes = Recipe.query.all()
            q = query.lower()
            recipe_list = [r for r in all_recipes if
                           q in r.title.lower() or q in (r.description or '').lower() or q in (
                                       r.tags or '').lower() or any(
                               q in (ing.product.name.lower() if ing.product else '') for ing in r.ingredients)]
            # сортируем и пагинируем
            recipe_list.sort(key=lambda x: x.created_at, reverse=True)
            total_recipes = len(recipe_list)
            start = (page - 1) * per_page
            recipes = recipe_list[start:start + per_page]
        if search_type in ('all', 'products'):
            all_products = Product.query.all()
            q = query.lower()
            product_list = [p for p in all_products if q in p.name.lower() or q in (p.category or '').lower()]
            product_list.sort(key=lambda x: x.name)
            total_products = len(product_list)
            start = (page - 1) * per_page
            products = product_list[start:start + per_page]

    return render_template(
        'search_results.html',
        query=query,
        search_type=search_type,
        recipes=recipes,
        products=products,
        total_recipes=total_recipes,
        total_products=total_products,
        page=page,
        per_page=per_page
    )