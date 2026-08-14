from flask import Flask
from config import Config
from database import db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация БД
    db.init_app(app)

    # Регистрация blueprints
    from routes.main import main_bp
    from routes.recipes import recipes_bp
    from routes.products import products_bp
    from routes.api import api_bp
    from routes.diary import diary_bp

    app.register_blueprint(diary_bp, url_prefix='/diary')
    app.register_blueprint(main_bp)
    app.register_blueprint(recipes_bp, url_prefix='/recipes')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Создание таблиц и папки uploads
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Контекстный процессор для шаблонов
    @app.context_processor
    def utility_processor():
        from models import Product, Recipe
        return {
            'all_products': Product.query.order_by(Product.name).all(),
            'all_recipes': Recipe.query.order_by(Recipe.title).all()

        }

    return app



if __name__ == '__main__':
    application = create_app()
    print("=" * 60)
    print("  RecipeCalc - приложение для расчёта КБЖУ рецептов")
    print("  Откройте в браузере: http://127.0.0.1:5000")
    print("=" * 60)
    application.run(debug=True, host='0.0.0.0', port=5000)