# Руководство по тестированию

Подробное руководство по тестированию RAG-системы салона красоты.

## Содержание

- [Обзор тестирования](#обзор-тестирования)
- [Структура тестов](#структура-тестов)
- [Запуск тестов](#запуск-тестов)
- [Типы тестов](#типы-тестов)
- [Мок-объекты](#мок-объекты)
- [Покрытие кода](#покрытие-кода)
- [Написание новых тестов](#написание-новых-тестов)
- [Отладка тестов](#отладка-тестов)

## Обзор тестирования

Система тестирования включает:

- **Модульные тесты**: Тестирование отдельных функций и классов
- **Интеграционные тесты**: Тестирование взаимодействия между модулями
- **Тесты производительности**: Проверка работы с большими объемами данных
- **Тесты параллельности**: Проверка корректной работы в многопоточной среде
- **Smoke-тесты**: Быстрая проверка основной функциональности

## Структура тестов

```
tests/
├── __init__.py                 # Инициализация пакета тестов
├── test_config.py             # Тесты конфигурации
├── test_data_loader.py        # Тесты загрузчика данных
├── test_search_module.py      # Тесты поискового модуля
├── test_consultation_module.py # Тесты консультационного модуля
├── test_gpt_client.py         # Тесты GPT клиента
├── test_main.py               # Тесты главного модуля
├── test_integration.py        # Интеграционные тесты
├── test_mocks.py             # Мок-объекты и фикстуры
├── test_logger.py            # Тесты системы логирования
└── test_error_handler.py     # Тесты обработки ошибок
```

## Запуск тестов

### Использование run_tests.py

```bash
# Все тесты с полной проверкой
python run_tests.py --all

# Только модульные тесты
python run_tests.py --unit

# Интеграционные тесты
python run_tests.py --integration

# Тесты производительности
python run_tests.py --performance

# Smoke-тесты (быстрая проверка)
python run_tests.py --smoke

# С анализом покрытия кода
python run_tests.py --unit --coverage

# Конкретный файл тестов
python run_tests.py --file test_data_loader.py

# С подробным выводом
python run_tests.py --unit --verbose

# Проверка качества кода
python run_tests.py --lint

# Генерация полного отчета
python run_tests.py --report
```

### Прямое использование pytest

```bash
# Все тесты
pytest tests/

# Конкретный файл
pytest tests/test_data_loader.py

# Конкретный тест
pytest tests/test_data_loader.py::TestDataLoader::test_load_services_json_success

# С покрытием
pytest tests/ --cov=beauty_salon_rag --cov-report=html

# С подробным выводом
pytest tests/ -v

# Остановка на первой ошибке
pytest tests/ -x

# Запуск в параллельном режиме (требует pytest-xdist)
pytest tests/ -n auto
```

## Типы тестов

### 1. Модульные тесты

Тестируют отдельные функции и классы в изоляции.

**Пример:**
```python
def test_load_services_json_success(self):
    """Тест успешной загрузки services.json."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем тестовый файл
        services_file = Path(temp_dir) / "services.json"
        with open(services_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_services_data, f)
        
        # Тестируем загрузку
        loader = DataLoader(temp_dir)
        data = loader.load_services_json()
        
        self.assertEqual(data, self.test_services_data)
```

**Характеристики:**
- Быстрые (< 1 секунды на тест)
- Изолированные (используют моки для внешних зависимостей)
- Детальные (тестируют конкретные сценарии)

### 2. Интеграционные тесты

Тестируют взаимодействие между модулями.

**Пример:**
```python
def test_search_to_consultation_flow(self, mock_consultation_gpt, mock_search_gpt, test_data_files):
    """Тест полного потока от поиска к консультации."""
    # Настройка моков GPT
    mock_search_gpt_instance.search_services.return_value = ["massage-face-1"]
    mock_consultation_gpt_instance.generate_response.return_value = "Консультационный ответ"
    
    # Создание модулей с реальными файлами
    search_module = SearchModule(test_data_files['temp_dir'])
    consultation_module = ConsultationModule(test_data_files['temp_dir'])
    
    # Выполнение полного цикла
    service_ids = search_module.find_services("массаж лица")
    response = consultation_module.generate_consultation_response("массаж лица", service_ids)
    
    assert "консультационный ответ" in response.lower()
```

**Характеристики:**
- Средняя скорость (1-5 секунд на тест)
- Используют реальные файлы данных
- Тестируют полные сценарии использования

### 3. Тесты производительности

Проверяют работу системы под нагрузкой.

**Пример:**
```python
def test_large_dataset_loading_performance(self, large_test_data):
    """Тест производительности загрузки большого набора данных."""
    import time
    
    data_loader = DataLoader(large_test_data)
    
    # Измеряем время загрузки
    start_time = time.time()
    services_data = data_loader.load_services_json()
    load_time = time.time() - start_time
    
    assert len(services_data["data"]["items"]) == 100
    assert load_time < 1.0  # Должно загружаться менее чем за 1 секунду
```

**Характеристики:**
- Медленные (5-30 секунд на тест)
- Используют большие объемы данных
- Проверяют временные и ресурсные ограничения

### 4. Тесты параллельности

Проверяют корректную работу в многопоточной среде.

**Пример:**
```python
def test_concurrent_data_loading(self, concurrent_test_data):
    """Тест параллельной загрузки данных."""
    import threading
    
    results = []
    errors = []
    
    def load_data():
        try:
            loader = DataLoader(concurrent_test_data)
            data = loader.load_services_json()
            results.append(len(data["data"]["items"]))
        except Exception as e:
            errors.append(e)
    
    # Создаем 10 потоков
    threads = [threading.Thread(target=load_data) for _ in range(10)]
    
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    assert len(errors) == 0
    assert all(result == 10 for result in results)
```

## Мок-объекты

### Использование встроенных моков

Файл `tests/test_mocks.py` содержит готовые мок-объекты:

```python
from tests.test_mocks import MockGPTClient, MockDataLoader, create_test_services_data

# Использование мок GPT клиента
mock_gpt = MockGPTClient()
service_ids = mock_gpt.search_services("массаж лица", {})

# Использование мок загрузчика данных
mock_loader = MockDataLoader()
services = mock_loader.load_services_json()

# Создание тестовых данных
test_data = create_test_services_data()
```

### Создание собственных моков

```python
from unittest.mock import Mock, patch

# Мокирование метода
with patch('beauty_salon_rag.gpt_client.OpenAI') as mock_openai:
    mock_client = Mock()
    mock_openai.return_value = mock_client
    
    # Настройка поведения мока
    mock_client.chat.completions.create.return_value = mock_response
    
    # Тестирование
    gpt_client = GPTClient()
    result = gpt_client.search_services("test", {})

# Мокирование с side_effect для исключений
mock_method.side_effect = Exception("Test error")
```

### Фикстуры pytest

```python
@pytest.fixture
def mock_services_data():
    """Фикстура с тестовыми данными услуг."""
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": "test-service-1",
                    "title": "Тестовая услуга",
                    "price": 1000
                }
            ]
        }
    }

@pytest.fixture
def temp_services_file(tmp_path, mock_services_data):
    """Создает временный файл с тестовыми данными."""
    services_file = tmp_path / "services.json"
    with open(services_file, 'w', encoding='utf-8') as f:
        json.dump(mock_services_data, f, ensure_ascii=False)
    return str(tmp_path)
```

## Покрытие кода

### Генерация отчета о покрытии

```bash
# HTML отчет
pytest tests/ --cov=beauty_salon_rag --cov-report=html:htmlcov

# Терминальный отчет
pytest tests/ --cov=beauty_salon_rag --cov-report=term-missing

# XML отчет (для CI/CD)
pytest tests/ --cov=beauty_salon_rag --cov-report=xml
```

### Анализ покрытия

После генерации HTML отчета откройте `htmlcov/index.html` в браузере для детального анализа:

- **Зеленые строки**: Покрыты тестами
- **Красные строки**: Не покрыты тестами
- **Желтые строки**: Частично покрыты (например, не все ветки условий)

### Цели покрытия

- **Общее покрытие**: > 90%
- **Критические модули**: > 95%
- **Новый код**: 100%

## Написание новых тестов

### Структура теста

```python
class TestNewFeature:
    """Тесты для новой функциональности."""
    
    @pytest.fixture
    def setup_data(self):
        """Подготовка данных для тестов."""
        return {"test": "data"}
    
    def test_positive_case(self, setup_data):
        """Тест позитивного сценария."""
        # Arrange (подготовка)
        input_data = setup_data
        expected_result = "expected"
        
        # Act (выполнение)
        result = function_under_test(input_data)
        
        # Assert (проверка)
        assert result == expected_result
    
    def test_negative_case(self):
        """Тест негативного сценария."""
        with pytest.raises(ExpectedException):
            function_under_test(invalid_input)
    
    def test_edge_case(self):
        """Тест граничного случая."""
        result = function_under_test(edge_case_input)
        assert result is not None
```

### Соглашения по именованию

- **Файлы тестов**: `test_<module_name>.py`
- **Классы тестов**: `Test<ClassName>`
- **Методы тестов**: `test_<what_is_being_tested>`
- **Фикстуры**: `<descriptive_name>` (без префикса test_)

### Лучшие практики

1. **Один тест - одна проверка**
   ```python
   # Хорошо
   def test_user_creation_success(self):
       user = create_user("test@example.com")
       assert user.email == "test@example.com"
   
   def test_user_creation_validation(self):
       with pytest.raises(ValidationError):
           create_user("invalid-email")
   
   # Плохо
   def test_user_creation(self):
       user = create_user("test@example.com")
       assert user.email == "test@example.com"
       
       with pytest.raises(ValidationError):
           create_user("invalid-email")
   ```

2. **Описательные имена тестов**
   ```python
   # Хорошо
   def test_load_services_json_returns_correct_data_structure(self):
   
   # Плохо
   def test_load_services(self):
   ```

3. **Использование фикстур для подготовки данных**
   ```python
   @pytest.fixture
   def sample_service_data():
       return {"id": "test-1", "title": "Test Service"}
   
   def test_service_processing(sample_service_data):
       result = process_service(sample_service_data)
       assert result is not None
   ```

4. **Тестирование исключений**
   ```python
   def test_invalid_input_raises_validation_error(self):
       with pytest.raises(ValidationError, match="Invalid input format"):
           validate_input("invalid")
   ```

## Отладка тестов

### Запуск отдельного теста

```bash
# Конкретный тест
pytest tests/test_data_loader.py::TestDataLoader::test_load_services_json_success -v

# С отладочным выводом
pytest tests/test_data_loader.py::TestDataLoader::test_load_services_json_success -v -s

# С pdb отладчиком
pytest tests/test_data_loader.py::TestDataLoader::test_load_services_json_success --pdb
```

### Использование print для отладки

```python
def test_debug_example(self):
    data = load_test_data()
    print(f"Loaded data: {data}")  # Будет видно с флагом -s
    
    result = process_data(data)
    print(f"Result: {result}")
    
    assert result is not None
```

### Логирование в тестах

```python
import logging

def test_with_logging(caplog):
    with caplog.at_level(logging.INFO):
        function_that_logs()
    
    assert "Expected log message" in caplog.text
```

### Временные файлы и директории

```python
import tempfile
from pathlib import Path

def test_with_temp_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.json"
        test_file.write_text('{"test": "data"}')
        
        # Тестирование с временным файлом
        result = process_file(test_file)
        assert result is not None
```

## Непрерывная интеграция

### GitHub Actions пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: python run_tests.py --all
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Метрики качества

### Целевые показатели

- **Покрытие кода**: > 90%
- **Время выполнения модульных тестов**: < 30 секунд
- **Время выполнения всех тестов**: < 5 минут
- **Количество падающих тестов**: 0
- **Flaky тесты**: < 1%

### Мониторинг качества

```bash
# Проверка покрытия
python run_tests.py --unit --coverage

# Проверка производительности тестов
pytest tests/ --durations=10

# Проверка качества кода
python run_tests.py --lint

# Полный отчет
python run_tests.py --report
```

## Устранение неполадок

### Частые проблемы

1. **Тесты падают локально, но проходят в CI**
   - Проверьте переменные окружения
   - Убедитесь в одинаковых версиях зависимостей
   - Проверьте различия в файловых системах

2. **Медленные тесты**
   - Используйте моки вместо реальных API вызовов
   - Оптимизируйте создание тестовых данных
   - Рассмотрите параллельный запуск тестов

3. **Flaky тесты**
   - Избегайте зависимости от времени
   - Используйте детерминированные данные
   - Правильно очищайте состояние между тестами

4. **Проблемы с импортами**
   - Убедитесь, что PYTHONPATH настроен правильно
   - Проверьте структуру пакетов
   - Используйте относительные импорты в тестах

### Полезные команды для отладки

```bash
# Запуск с максимальной детализацией
pytest tests/ -vvv

# Показать все print выводы
pytest tests/ -s

# Остановиться на первой ошибке
pytest tests/ -x

# Запустить только упавшие тесты
pytest tests/ --lf

# Показать самые медленные тесты
pytest tests/ --durations=0

# Запуск с профилированием
pytest tests/ --profile
```