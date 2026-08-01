// ===== RECIPECALC - ГЛАВНЫЙ СКРИПТ =====

document.addEventListener('DOMContentLoaded', function () {
    console.log('🥗 RecipeCalc initialized');

    // Flash-сообщения - автоскрытие
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    // Рейтинг звёздами
    initStarRating();

    // Масштабирование порций
    initPortionScaler();

    // Таймеры в шагах
    initStepTimers();

    // Избранное
    initFavorites();

    // Подтверждение удаления
    initDeleteConfirmation();
});

// ===== РЕЙТИНГ ЗВЁЗДАМИ =====
function initStarRating() {
    const starContainers = document.querySelectorAll('.stars[data-recipe-id]');
    starContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const recipeId = container.dataset.recipeId;

        stars.forEach(star => {
            star.addEventListener('click', function () {
                const score = parseInt(this.dataset.value);
                // Отправляем оценку на сервер
                fetch(`/recipes/${recipeId}/rate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ score: score })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            // Обновляем отображение звёзд
                            stars.forEach(s => {
                                if (parseInt(s.dataset.value) <= score) {
                                    s.classList.add('active');
                                } else {
                                    s.classList.remove('active');
                                }
                            });
                            // Обновляем счётчик
                            const countEl = container.parentElement.querySelector('.rating-count');
                            if (countEl) {
                                countEl.textContent = `(${data.rating_count}) ${data.rating}`;
                            }
                        }
                    })
                    .catch(err => console.error('Rating error:', err));
            });

            // Hover эффект
            star.addEventListener('mouseenter', function () {
                const value = parseInt(this.dataset.value);
                stars.forEach(s => {
                    if (parseInt(s.dataset.value) <= value) {
                        s.style.color = '#ffd700';
                    }
                });
            });

            star.addEventListener('mouseleave', function () {
                stars.forEach(s => {
                    if (!s.classList.contains('active')) {
                        s.style.color = '';
                    }
                });
            });
        });
    });
}

// ===== МАСШТАБИРОВАНИЕ ПОРЦИЙ =====
function initPortionScaler() {
    const scaler = document.getElementById('portion-scaler');
    if (!scaler) return;

    const recipeId = scaler.dataset.recipeId;
    const portionDisplay = document.getElementById('portion-display');
    const ingredientRows = document.querySelectorAll('.ingredient-row');

    // Сохраняем оригинальные количества
    const originalQuantities = [];
    ingredientRows.forEach(row => {
        const qtyEl = row.querySelector('.ingredient-quantity');
        if (qtyEl) {
            originalQuantities.push({
                row: row,
                originalQty: parseFloat(qtyEl.dataset.original || qtyEl.textContent)
            });
        }
    });

    scaler.addEventListener('input', function () {
        const newPortions = parseInt(this.value);
        if (portionDisplay) {
            portionDisplay.textContent = newPortions;
        }

        const originalPortions = parseInt(this.dataset.originalPortions || 1);
        const factor = newPortions / originalPortions;

        // Обновляем количества ингредиентов
        originalQuantities.forEach(item => {
            const qtyEl = item.row.querySelector('.ingredient-quantity');
            if (qtyEl) {
                const newQty = Math.round(item.originalQty * factor * 10) / 10;
                qtyEl.textContent = newQty;
            }
        });

        // Пересчитываем КБЖУ через API
        recalculateNutrition(recipeId, newPortions);
    });
}

function recalculateNutrition(recipeId, portions) {
    fetch(`/api/calculate-nutrition/${recipeId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ portions: portions })
    })
        .then(response => response.json())
        .then(data => {
            // Обновляем блок КБЖУ на странице
            const perPortionEl = document.getElementById('nutrition-per-portion');
            const per100gEl = document.getElementById('nutrition-per-100g');

            if (perPortionEl && data.per_portion) {
                perPortionEl.innerHTML = `
                    <div class="nutrition-value">${data.per_portion.calories}</div>
                    <div class="nutrition-label">ккал / порция</div>
                    <div style="font-size:0.8rem;color:var(--text-muted);margin-top:5px;">
                        Б: ${data.per_portion.proteins}г ·
                        Ж: ${data.per_portion.fats}г ·
                        У: ${data.per_portion.carbs}г
                    </div>
                `;
            }

            if (per100gEl && data.per_100g) {
                per100gEl.innerHTML = `
                    <div class="nutrition-value">${data.per_100g.calories}</div>
                    <div class="nutrition-label">ккал / 100г</div>
                `;
            }
        })
        .catch(err => console.error('Nutrition recalc error:', err));
}

// ===== ТАЙМЕРЫ В ШАГАХ =====
function initStepTimers() {
    const timerButtons = document.querySelectorAll('.start-timer-btn');
    timerButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const minutes = parseInt(this.dataset.minutes);
            const displayEl = this.parentElement.querySelector('.timer-display');
            startCountdown(minutes, displayEl, this);
        });
    });
}

function startCountdown(minutes, displayEl, button) {
    let totalSeconds = minutes * 60;
    button.disabled = true;
    button.textContent = '⏳ Идёт...';

    const interval = setInterval(() => {
        if (totalSeconds <= 0) {
            clearInterval(interval);
            displayEl.textContent = '✅ Готово!';
            displayEl.style.color = 'var(--neon-green)';
            button.textContent = '▶ Запустить';
            button.disabled = false;
            // Звуковое оповещение (вибрация если доступна)
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            }
            return;
        }

        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        displayEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
        totalSeconds--;
    }, 1000);
}

// ===== ИЗБРАННОЕ =====
function initFavorites() {
    const favButtons = document.querySelectorAll('.favorite-btn');
    favButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const recipeId = this.dataset.recipeId;

            fetch(`/recipes/${recipeId}/toggle-favorite`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'ok') {
                        const icon = this.querySelector('.fav-icon');
                        if (data.is_favorite) {
                            this.classList.add('active');
                            if (icon) icon.textContent = '❤️';
                        } else {
                            this.classList.remove('active');
                            if (icon) icon.textContent = '🤍';
                        }
                    }
                })
                .catch(err => console.error('Favorite error:', err));
        });
    });
}

// ===== ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ =====
function initDeleteConfirmation() {
    const deleteForms = document.querySelectorAll('form[data-confirm]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const message = this.dataset.confirm || 'Вы уверены?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// ===== ПОИСК ПРОДУКТОВ ДЛЯ АВТОДОПОЛНЕНИЯ =====
function searchProducts(query, callback) {
    if (query.length < 2) {
        callback([]);
        return;
    }

    fetch(`/api/search-products?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => callback(data))
        .catch(err => {
            console.error('Search error:', err);
            callback([]);
        });
}

// ===== ДОБАВЛЕНИЕ ИНГРЕДИЕНТА В ФОРМУ РЕЦЕПТА =====
function addIngredientRow(productId = '', productName = '', quantity = '', unit = 'г') {
    const container = document.getElementById('ingredients-container');
    if (!container) return;

    const index = container.children.length;
    const row = document.createElement('div');
    row.className = 'ingredient-row d-flex gap-2 align-items-center mb-2';
    row.innerHTML = `
        <select name="ingredient_product[]" class="form-control" style="flex:2;" required>
            <option value="">Выберите продукт...</option>
        </select>
        <input type="number" name="ingredient_quantity[]" class="form-control"
               style="flex:1;" placeholder="Кол-во" step="0.1" min="0" value="${quantity}" required>
        <select name="ingredient_unit[]" class="form-control" style="flex:0.5;">
            <option value="г" ${unit === 'г' ? 'selected' : ''}>г</option>
            <option value="мл" ${unit === 'мл' ? 'selected' : ''}>мл</option>
            <option value="шт" ${unit === 'шт' ? 'selected' : ''}>шт</option>
            <option value="ст.л." ${unit === 'ст.л.' ? 'selected' : ''}>ст.л.</option>
            <option value="ч.л." ${unit === 'ч.л.' ? 'selected' : ''}>ч.л.</option>
        </select>
        <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('.ingredient-row').remove()">
            ✕
        </button>
    `;

    container.appendChild(row);

    // Заполняем селект продуктами
    const select = row.querySelector('select[name="ingredient_product[]"]');
    if (select) {
        // Копируем опции из первого селекта или загружаем
        const firstSelect = container.querySelector('select[name="ingredient_product[]"]');
        if (firstSelect && firstSelect !== select) {
            select.innerHTML = firstSelect.innerHTML;
        }
        if (productId) {
            select.value = productId;
        }
    }
}

// ===== ДОБАВЛЕНИЕ ШАГА В ФОРМУ РЕЦЕПТА =====
function addStepRow(instruction = '', timerMinutes = 0) {
    const container = document.getElementById('steps-container');
    if (!container) return;

    const index = container.children.length + 1;
    const row = document.createElement('div');
    row.className = 'step-row mb-3 p-3';
    row.style.cssText = 'background: var(--bg-secondary); border-radius: var(--radius-md);';
    row.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <strong style="color: var(--neon-blue);">Шаг ${index}</strong>
            <button type="button" class="btn btn-danger btn-sm"
                    onclick="this.closest('.step-row').remove(); updateStepNumbers();">✕</button>
        </div>
        <div class="form-group">
            <textarea name="step_text[]" class="form-control"
                      placeholder="Опишите шаг приготовления..." rows="2">${instruction}</textarea>
        </div>
        <div class="form-group">
            <label class="form-label">Таймер (минуты, 0 = без таймера)</label>
            <input type="number" name="step_time[]" class="form-control"
                   value="${timerMinutes}" min="0" style="width:150px;">
        </div>
    `;

    container.appendChild(row);
}

function updateStepNumbers() {
    const container = document.getElementById('steps-container');
    if (!container) return;
    const rows = container.querySelectorAll('.step-row');
    rows.forEach((row, i) => {
        const strong = row.querySelector('strong');
        if (strong) strong.textContent = `Шаг ${i + 1}`;
    });
}