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

    // Таймеры в шагах
    initStepTimers();

    // Избранное
    initFavorites();

    // Подтверждение удаления
    initDeleteConfirmation();
});

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
        // Когда осталось меньше минуты - меняем цвет
        if (totalSeconds <= 60) {
            displayEl.style.color = 'var(--neon-orange)';
        }
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

// ===== ДОБАВЛЕНИЕ ИНГРЕДИЕНТА В ФОРМУ РЕЦЕПТА =====
function addIngredientRow(productId = '', productName = '', quantity = '', unit = 'г') {
    const container = document.getElementById('ingredients-container');
    if (!container) return;

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

// ===== Autocomplete =====
class Autocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.apiUrl = options.apiUrl || '/api/search-products';
        this.placeholder = options.placeholder || 'Начните вводить...';
        this.minLength = options.minLength || 0; // 0 - показывать всё при фокусе
        this.showAllOnFocus = options.showAllOnFocus !== undefined ? options.showAllOnFocus : true;
        this.onSelect = options.onSelect || function(item) {};
        this.valueField = options.valueField || 'id';
        this.labelField = options.labelField || 'name';

        this.dropdown = null;
        this.hiddenInput = null;
        this.selectedItem = null;
        this.isOpen = false;

        this.init();
    }

    init() {
        // Создаём скрытый input для хранения id
        this.hiddenInput = document.createElement('input');
        this.hiddenInput.type = 'hidden';
        this.hiddenInput.name = this.input.name + '_id';
        this.input.parentNode.insertBefore(this.hiddenInput, this.input.nextSibling);

        // Убираем оригинальный name, чтобы не отправлялся текст
        this.input.removeAttribute('name');
        this.input.setAttribute('autocomplete', 'off');
        this.input.setAttribute('placeholder', this.placeholder);

        // Создаём контейнер для выпадающего списка
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'autocomplete-dropdown';
        this.dropdown.style.display = 'none';
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.dropdown);

        // Обработчики событий
        this.input.addEventListener('input', this.debounce(() => this.fetchSuggestions(), 300));
        this.input.addEventListener('focus', () => {
            // При фокусе показываем все элементы, если поле пустое и опция включена
            if (this.showAllOnFocus && this.input.value.trim() === '') {
                this.fetchSuggestions(true);
            } else if (this.input.value.length >= this.minLength) {
                this.fetchSuggestions();
            }
        });
        // Если уже есть значение (при редактировании), можно установить
    }

    async fetchSuggestions(forceAll = false) {
        let query = this.input.value.trim();
        if (forceAll) {
            query = ''; // Отправим пустой запрос, чтобы получить всё
        }
        if (!forceAll && query.length < this.minLength) {
            this.close();
            return;
        }

        try {
            const url = `${this.apiUrl}?q=${encodeURIComponent(query)}`;
            const response = await fetch(url);
            const data = await response.json();
            this.renderDropdown(data);
        } catch (err) {
            console.error('Autocomplete error:', err);
        }
    }

    renderDropdown(items) {
        if (!items || items.length === 0) {
            this.close();
            return;
        }

        this.dropdown.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'autocomplete-item';
            div.textContent = item[this.labelField];
            div.addEventListener('click', () => this.selectItem(item));
            this.dropdown.appendChild(div);
        });

        this.dropdown.style.display = 'block';
        this.isOpen = true;
    }

    selectItem(item) {
        this.input.value = item[this.labelField];
        this.hiddenInput.value = item[this.valueField];
        this.selectedItem = item;
        this.close();
        if (this.onSelect) this.onSelect(item);
    }

    close() {
        this.dropdown.style.display = 'none';
        this.isOpen = false;
    }

    handleKeyboard(e) {
        if (!this.isOpen) return;
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        if (!items.length) return;

        const current = this.dropdown.querySelector('.autocomplete-item.active');
        let index = Array.from(items).indexOf(current);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            index = (index + 1) % items.length;
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            index = (index - 1 + items.length) % items.length;
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (current) {
                current.click();
            }
            return;
        } else if (e.key === 'Escape') {
            this.close();
            return;
        } else {
            return;
        }

        items.forEach(item => item.classList.remove('active'));
        items[index].classList.add('active');
        items[index].scrollIntoView({ block: 'nearest' });
    }

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Установить значение извне (для редактирования)
    setValue(id, label) {
        this.input.value = label;
        this.hiddenInput.value = id;
        this.selectedItem = { [this.valueField]: id, [this.labelField]: label };
    }
}