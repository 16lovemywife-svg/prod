from flask import Blueprint, render_template, request
from models import Recipe, Product
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Главная страница с поиском и отображением рецептов"""
    search_query = request.args.get('q', '')
    category_filter = request.args.get('category', '')
    difficulty_filter = request.args.get('difficulty', '')
    sort_by = request.args.get('sort', 'newest')

    # Базовый запрос
    query = Recipe.query

    # Поиск по названию и тегам
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

    # Сортировка
    if sort_by == 'rating':
        query = query.order_by(Recipe.rating.desc())
    elif sort_by == 'quick':
        query = query.order_by(Recipe.total_time.asc())
    elif sort_by == 'calories':
        query = query.order_by(Recipe.id)  # Заглушка, нужна денормализация
    else:  # newest
        query = query.order_by(Recipe.created_at.desc())

    recipes = query.limit(50).all()

    # Популярные категории для hero-блока
    categories = [
        {'name': 'Завтраки', 'icon': '🌅', 'tag': 'завтрак'},
        {'name': 'Салаты', 'icon': '🥗', 'tag': 'салат'},
        {'name': 'Супы', 'icon': '🍲', 'tag': 'суп'},
        {'name': 'Горячее', 'icon': '🍖', 'tag': 'горячее'},
        {'name': 'Десерты', 'icon': '🍰', 'tag': 'десерт'},
        {'name': 'Напитки', 'icon': '🍹', 'tag': 'напиток'},
    ]

    # Статистика для отображения
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
        sort_by=sort_by
    )