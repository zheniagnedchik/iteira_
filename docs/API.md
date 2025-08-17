# API Документация

Подробная документация по API всех модулей RAG-системы салона красоты.

## Содержание

- [DataLoader API](#dataloader-api)
- [SearchModule API](#searchmodule-api)
- [ConsultationModule API](#consultationmodule-api)
- [GPTClient API](#gptclient-api)
- [Config API](#config-api)
- [Logger API](#logger-api)
- [Error Handler API](#error-handler-api)

## DataLoader API

### Класс DataLoader

Отвечает за загрузку и работу с JSON файлами данных.

#### Конструктор

```python
DataLoader(base_path: str = ".")
```

**Параметры:**
- `base_path` (str): Базовый путь к файлам данных

#### Методы

##### load_services_json()

```python
load_services_json(force_reload: bool = False) -> Dict[str, Any]
```

Загружает полные данные услуг из services.json.

**Параметры:**
- `force_reload` (bool): Принудительная перезагрузка данных

**Возвращает:**
- `Dict[str, Any]`: Словарь с данными услуг

**Исключения:**
- `DataLoadError`: При ошибке загрузки файла

##### load_services_no_staff_json()

```python
load_services_no_staff_json(force_reload: bool = False) -> Dict[str, Any]
```

Загружает облегченные данные услуг из services_no_staff.json.

**Параметры:**
- `force_reload` (bool): Принудительная перезагрузка данных

**Возвращает:**
- `Dict[str, Any]`: Словарь с данными услуг без персонала

**Исключения:**
- `DataLoadError`: При ошибке загрузки файла

##### get_services_by_ids()

```python
get_services_by_ids(service_ids: List[str]) -> List[Dict[str, Any]]
```

Получает услуги по массиву ID из полного файла services.json.

**Параметры:**
- `service_ids` (List[str]): Список ID услуг для поиска

**Возвращает:**
- `List[Dict[str, Any]]`: Список найденных услуг

**Исключения:**
- `DataLoadError`: При ошибке загрузки данных
- `ValidationError`: При некорректных входных параметрах

##### validate_service_exists()

```python
validate_service_exists(service_id: str) -> bool
```

Проверяет существование услуги по ID.

**Параметры:**
- `service_id` (str): ID услуги для проверки

**Возвращает:**
- `bool`: True если услуга существует, False иначе

##### get_all_service_ids()

```python
get_all_service_ids() -> List[str]
```

Получает список всех ID услуг.

**Возвращает:**
- `List[str]`: Список всех ID услуг

##### clear_cache()

```python
clear_cache() -> None
```

Очищает кэш загруженных данных.

### Удобные функции

#### load_services()

```python
load_services() -> Dict[str, Any]
```

Быстрая загрузка services.json.

#### load_services_no_staff()

```python
load_services_no_staff() -> Dict[str, Any]
```

Быстрая загрузка services_no_staff.json.

#### find_services_by_ids()

```python
find_services_by_ids(service_ids: List[str]) -> List[Dict[str, Any]]
```

Быстрый поиск услуг по ID.

## SearchModule API

### Класс SearchModule

Обеспечивает поиск релевантных услуг в облегченном файле через GPT.

#### Конструктор

```python
SearchModule(base_path: str = ".")
```

**Параметры:**
- `base_path` (str): Базовый путь к файлам данных

**Исключения:**
- `SearchModuleError`: При ошибке инициализации

#### Методы

##### load_light_services()

```python
load_light_services() -> Dict[str, Any]
```

Загружает облегченные данные услуг.

**Возвращает:**
- `Dict[str, Any]`: Словарь с данными услуг без персонала

**Исключения:**
- `SearchModuleError`: При ошибке загрузки данных

##### find_services()

```python
find_services(query: str) -> List[str]
```

Находит релевантные услуги по текстовому запросу через GPT.

**Параметры:**
- `query` (str): Поисковый запрос пользователя

**Возвращает:**
- `List[str]`: Список ID найденных услуг

**Исключения:**
- `SearchModuleError`: При ошибке поиска
- `ValidationError`: При некорректных входных параметрах

##### get_service_details_by_ids()

```python
get_service_details_by_ids(service_ids: List[str]) -> List[Dict[str, Any]]
```

Получает детальную информацию об услугах по их ID из облегченного файла.

**Параметры:**
- `service_ids` (List[str]): Список ID услуг

**Возвращает:**
- `List[Dict[str, Any]]`: Список словарей с информацией об услугах

**Исключения:**
- `SearchModuleError`: При ошибке получения данных

##### search_with_details()

```python
search_with_details(query: str) -> List[Dict[str, Any]]
```

Выполняет поиск и возвращает детальную информацию об найденных услугах.

**Параметры:**
- `query` (str): Поисковый запрос пользователя

**Возвращает:**
- `List[Dict[str, Any]]`: Список словарей с детальной информацией об услугах

**Исключения:**
- `SearchModuleError`: При ошибке поиска или получения данных

##### health_check()

```python
health_check() -> bool
```

Проверяет работоспособность поискового модуля.

**Возвращает:**
- `bool`: True если модуль работает корректно, False иначе

### Удобные функции

#### search_services()

```python
search_services(query: str, base_path: str = ".") -> List[str]
```

Быстрый поиск услуг по запросу.

#### search_services_with_details()

```python
search_services_with_details(query: str, base_path: str = ".") -> List[Dict[str, Any]]
```

Быстрый поиск услуг с получением детальной информации.

## ConsultationModule API

### Класс ConsultationModule

Обеспечивает консультирование клиентов на основе полных данных об услугах.

#### Конструктор

```python
ConsultationModule(base_path: str = ".")
```

**Параметры:**
- `base_path` (str): Базовый путь к файлам данных

**Исключения:**
- `ConsultationModuleError`: При ошибке инициализации

#### Методы

##### load_full_services()

```python
load_full_services() -> Dict[str, Any]
```

Загружает полные данные услуг из services.json.

**Возвращает:**
- `Dict[str, Any]`: Словарь с полными данными услуг

**Исключения:**
- `ConsultationModuleError`: При ошибке загрузки данных

##### get_services_by_ids()

```python
get_services_by_ids(service_ids: List[str]) -> List[Dict[str, Any]]
```

Получает полную информацию об услугах по их ID.

**Параметры:**
- `service_ids` (List[str]): Список ID услуг

**Возвращает:**
- `List[Dict[str, Any]]`: Список словарей с полной информацией об услугах

**Исключения:**
- `ConsultationModuleError`: При ошибке получения данных
- `ValueError`: При некорректных входных параметрах

##### format_staff_info()

```python
format_staff_info(service: Dict[str, Any]) -> Dict[str, Any]
```

Форматирует информацию о мастерах и датах записи для услуги.

**Параметры:**
- `service` (Dict[str, Any]): Словарь с данными услуги

**Возвращает:**
- `Dict[str, Any]`: Словарь с отформатированной информацией о мастерах

##### format_service_details()

```python
format_service_details(service: Dict[str, Any]) -> Dict[str, Any]
```

Форматирует детальную информацию об услуге для консультации.

**Параметры:**
- `service` (Dict[str, Any]): Словарь с данными услуги

**Возвращает:**
- `Dict[str, Any]`: Словарь с отформатированной информацией об услуге

##### generate_consultation_response()

```python
generate_consultation_response(query: str, service_ids: List[str]) -> str
```

Генерирует консультационный ответ на основе найденных услуг.

**Параметры:**
- `query` (str): Запрос клиента
- `service_ids` (List[str]): Список ID найденных услуг

**Возвращает:**
- `str`: Сгенерированный ответ консультанта

**Исключения:**
- `ConsultationModuleError`: При ошибке генерации ответа
- `ValidationError`: При некорректных входных параметрах

##### get_booking_info()

```python
get_booking_info(service_ids: List[str]) -> Dict[str, Any]
```

Получает информацию о записи для указанных услуг.

**Параметры:**
- `service_ids` (List[str]): Список ID услуг

**Возвращает:**
- `Dict[str, Any]`: Словарь с информацией о доступных мастерах и датах

**Исключения:**
- `ConsultationModuleError`: При ошибке получения данных

##### health_check()

```python
health_check() -> bool
```

Проверяет работоспособность консультационного модуля.

**Возвращает:**
- `bool`: True если модуль работает корректно, False иначе

### Удобные функции

#### get_consultation_response()

```python
get_consultation_response(query: str, service_ids: List[str], base_path: str = ".") -> str
```

Быстрое получение консультационного ответа.

#### get_services_with_staff_info()

```python
get_services_with_staff_info(service_ids: List[str], base_path: str = ".") -> List[Dict[str, Any]]
```

Быстрое получение услуг с информацией о мастерах.

## GPTClient API

### Класс GPTClient

Клиент для взаимодействия с OpenAI GPT API.

#### Конструктор

```python
GPTClient()
```

**Исключения:**
- `ConfigurationError`: При отсутствии API ключа
- `GPTClientError`: При ошибке инициализации OpenAI клиента

#### Методы

##### search_services()

```python
search_services(query: str, services_data: Dict[str, Any]) -> List[str]
```

Поиск релевантных услуг с использованием GPT.

**Параметры:**
- `query` (str): Поисковый запрос пользователя
- `services_data` (Dict[str, Any]): Словарь с данными услуг

**Возвращает:**
- `List[str]`: Список ID услуг, соответствующих запросу

**Исключения:**
- `GPTClientError`: При ошибке поиска или некорректном формате ответа
- `ValidationError`: При некорректных входных параметрах

##### generate_response()

```python
generate_response(query: str, found_services: List[Dict[str, Any]]) -> str
```

Генерация консультационного ответа с использованием GPT.

**Параметры:**
- `query` (str): Запрос пользователя
- `found_services` (List[Dict[str, Any]]): Список данных найденных услуг

**Возвращает:**
- `str`: Сгенерированный текст ответа

**Исключения:**
- `GPTClientError`: При ошибке генерации ответа
- `ValidationError`: При некорректных входных параметрах

##### health_check()

```python
health_check() -> bool
```

Проверка работоспособности GPT клиента.

**Возвращает:**
- `bool`: True если клиент работает корректно, False иначе

## Config API

### Класс Config

Управление конфигурацией приложения.

#### Конструктор

```python
Config()
```

#### Методы

##### get()

```python
get(key: str, default: Any = None) -> Any
```

Получение значения конфигурации по ключу с использованием точечной нотации.

**Параметры:**
- `key` (str): Ключ конфигурации (например, "openai.model")
- `default` (Any): Значение по умолчанию

**Возвращает:**
- `Any`: Значение конфигурации или значение по умолчанию

##### get_openai_key()

```python
get_openai_key() -> str
```

Получение OpenAI API ключа.

**Возвращает:**
- `str`: API ключ OpenAI

**Исключения:**
- `ValueError`: Если API ключ не найден

##### get_openai_config()

```python
get_openai_config() -> Dict[str, Any]
```

Получение конфигурации OpenAI.

**Возвращает:**
- `Dict[str, Any]`: Словарь с настройками OpenAI

##### get_data_files()

```python
get_data_files() -> Dict[str, str]
```

Получение путей к файлам данных.

**Возвращает:**
- `Dict[str, str]`: Словарь с путями к файлам

### Глобальные функции

#### load_config()

```python
load_config() -> Config
```

Загрузка и возврат экземпляра конфигурации.

## Logger API

### Функции логирования

#### get_logger()

```python
get_logger(name: str) -> logging.Logger
```

Получение настроенного логгера.

**Параметры:**
- `name` (str): Имя логгера

**Возвращает:**
- `logging.Logger`: Настроенный логгер

#### setup_logging()

```python
setup_logging() -> None
```

Настройка системы логирования.

#### log_operation()

```python
log_operation(operation_name: str)
```

Декоратор для автоматического логирования операций.

**Параметры:**
- `operation_name` (str): Имя операции для логирования

**Пример использования:**
```python
@log_operation("load_data")
def load_data():
    # код функции
    pass
```

## Error Handler API

### Исключения

#### BeautySalonError

Базовое исключение для всех ошибок системы.

```python
BeautySalonError(
    message: str,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: str = None,
    **kwargs
)
```

#### DataLoadError

Исключение для ошибок загрузки данных.

#### GPTClientError

Исключение для ошибок GPT клиента.

#### ConfigurationError

Исключение для ошибок конфигурации.

#### ValidationError

Исключение для ошибок валидации.

### Функции

#### handle_error()

```python
handle_error(error: Exception, context: Dict[str, Any] = None) -> str
```

Централизованная обработка ошибок.

**Параметры:**
- `error` (Exception): Исключение для обработки
- `context` (Dict[str, Any]): Контекст ошибки

**Возвращает:**
- `str`: Пользовательское сообщение об ошибке

### Перечисления

#### ErrorCategory

- `SYSTEM`: Системные ошибки
- `API`: Ошибки внешних API
- `DATA`: Ошибки данных
- `USER`: Ошибки пользовательского ввода
- `BUSINESS`: Бизнес-логические ошибки

#### ErrorSeverity

- `LOW`: Низкая критичность
- `MEDIUM`: Средняя критичность
- `HIGH`: Высокая критичность
- `CRITICAL`: Критическая ошибка

## Примеры использования

### Полный пример работы с API

```python
from beauty_salon_rag.modules.data_loader import DataLoader
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.modules.consultation_module import ConsultationModule

# Инициализация модулей
data_loader = DataLoader()
search_module = SearchModule()
consultation_module = ConsultationModule()

# Загрузка данных
services = data_loader.load_services_json()
print(f"Загружено {len(services['data']['items'])} услуг")

# Поиск услуг
query = "массаж лица для омоложения"
service_ids = search_module.find_services(query)
print(f"Найдено {len(service_ids)} услуг: {service_ids}")

# Генерация консультационного ответа
if service_ids:
    response = consultation_module.generate_consultation_response(query, service_ids)
    print(f"Ответ: {response}")

# Получение информации о записи
booking_info = consultation_module.get_booking_info(service_ids)
print(f"Доступно мастеров: {len(booking_info['all_masters'])}")
```

### Обработка ошибок

```python
from beauty_salon_rag.error_handler import handle_error, DataLoadError

try:
    data_loader = DataLoader()
    services = data_loader.load_services_json()
except Exception as e:
    user_message = handle_error(e, context={"operation": "data_loading"})
    print(f"Ошибка: {user_message}")
```

### Логирование операций

```python
from beauty_salon_rag.logger import get_logger, log_operation

logger = get_logger(__name__)

@log_operation("custom_operation")
def my_function():
    logger.info("Выполнение пользовательской операции")
    # код функции
    return "результат"

result = my_function()
```