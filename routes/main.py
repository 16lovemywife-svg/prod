from flask import Blueprint, render_template, request
from models import Recipe, Product
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Главная страница с поиском, фильтрами и пагинацией"""
    search_query = request.args.get('q', '')
    difficulty_filter = request.args.get('difficulty', '')
    favorites_filter = request.args.get('favorites', '0')
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 12  # рецептов на странице

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

        # Фильтр по избранному ← добавить
    if favorites_filter == '1':
        query = query.filter(Recipe.favorites == True)

    # Сортировка
    if sort_by == 'quick':
        query = query.order_by(Recipe.total_time.asc())
    else:  # newest
        query = query.order_by(Recipe.created_at.desc())

    # Пагинация
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
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