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
        query = query.filter(
            or_(
                Recipe.title.ilike(f'%{search_query}%'),
                Recipe.description.ilike(f'%{search_query}%'),
                Recipe.tags.ilike(f'%{search_query}%')
            )
        )

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
            recipe_query = Recipe.query.filter(
                or_(
                    func.lower(Recipe.title).contains(query.lower()),
                    func.lower(Recipe.description).contains(query.lower()),
                    func.lower(Recipe.tags).contains(query.lower()),
                    Recipe.ingredients.any(
                        RecipeIngredient.product.has(
                            func.lower(Product.name).contains(query.lower())
                        )
                    )
                )
            ).order_by(Recipe.created_at.desc())

            recipe_pag = recipe_query.paginate(page=page, per_page=per_page, error_out=False)
            recipes = recipe_pag.items
            total_recipes = recipe_pag.total

        if search_type in ('all', 'products'):
            product_query = Product.query.filter(
                or_(
                    func.lower(Product.name).contains(query.lower()),
                    func.lower(Product.category).contains(query.lower())
                )
            ).order_by(Product.name)

            prod_pag = product_query.paginate(page=page, per_page=per_page, error_out=False)
            products = prod_pag.items
            total_products = prod_pag.total

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