"""
GPT Client module for Beauty Salon RAG System
Handles interaction with OpenAI API for search and consultation
"""

import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from openai.types.chat import ChatCompletion

from .config import config
from .logger import get_logger, log_operation
from .error_handler import GPTClientError, ConfigurationError, ValidationError


class GPTClient:
    """Client for interacting with OpenAI GPT API with performance optimizations"""
    
    def __init__(self):
        """Initialize GPT client with configuration"""
        self.logger = get_logger(__name__)
        
        # Get OpenAI configuration
        try:
            self.api_key = config.get_openai_key()
        except ValueError as e:
            self.logger.error(f"Failed to get OpenAI API key: {e}")
            raise ConfigurationError(
                f"Failed to get OpenAI API key: {e}",
                config_key="OPENAI_API_KEY"
            )
        
        openai_config = config.get_openai_config()
        
        self.model = openai_config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = openai_config.get('max_tokens', 1000)
        self.temperature = openai_config.get('temperature', 0.7)
        
        # Performance optimization settings
        self.request_timeout = 30  # Timeout for API requests
        self.max_retries = 3  # Maximum number of retries
        self.retry_delay = 1  # Initial delay between retries (exponential backoff)
        
        # Response caching for identical requests
        self._response_cache = {}
        self._cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        self._cache_timestamps = {}
        
        # Request rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # Minimum interval between requests (100ms)
        
        # Thread pool for concurrent requests
        self._executor = ThreadPoolExecutor(max_workers=3)
        
        # Initialize OpenAI client
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=self.request_timeout
            )
            self.logger.info("GPT client initialized successfully with performance optimizations")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise GPTClientError(
                f"Failed to initialize OpenAI client: {e}",
                api_error=str(e)
            )
    
    def _get_cache_key(self, messages: List[Dict[str, str]], 
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> str:
        """Generate cache key for request parameters"""
        cache_data = {
            'messages': messages,
            'temperature': temperature or self.temperature,
            'max_tokens': max_tokens or self.max_tokens,
            'model': self.model
        }
        return str(hash(json.dumps(cache_data, sort_keys=True)))
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        return (time.time() - cache_time) < self._cache_ttl
    
    def _rate_limit(self):
        """Apply rate limiting to prevent API overload"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    @log_operation("gpt_api_request")
    def _make_request(self, messages: List[Dict[str, str]], 
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     use_cache: bool = True) -> str:
        """
        Make a request to OpenAI API with performance optimizations
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            use_cache: Whether to use response caching
            
        Returns:
            Response content as string
            
        Raises:
            GPTClientError: If API request fails
        """
        # Валидация входных параметров
        if not isinstance(messages, list) or not messages:
            raise ValidationError(
                "Messages must be a non-empty list",
                field="messages",
                value=type(messages).__name__
            )
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                raise ValidationError(
                    f"Invalid message format at index {i}",
                    field=f"messages[{i}]",
                    value=str(message)
                )
        
        # Check cache first
        cache_key = None
        if use_cache:
            cache_key = self._get_cache_key(messages, temperature, max_tokens)
            if cache_key in self._response_cache and self._is_cache_valid(cache_key):
                self.logger.debug("Returning cached response")
                return self._response_cache[cache_key]
        
        # Apply rate limiting
        self._rate_limit()
        
        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Making GPT request (attempt {attempt + 1}/{self.max_retries}) with {len(messages)} messages")
                
                start_time = time.time()
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens
                )
                request_time = time.time() - start_time
                
                content = response.choices[0].message.content
                if not content:
                    raise GPTClientError(
                        "Empty response from OpenAI API",
                        details={"model": self.model, "messages_count": len(messages)}
                    )
                
                # Cache successful response
                if use_cache and cache_key:
                    self._response_cache[cache_key] = content
                    self._cache_timestamps[cache_key] = time.time()
                
                self.logger.debug(f"GPT response received: {len(content)} characters in {request_time:.2f}s")
                return content
                
            except Exception as e:
                last_exception = e
                api_error = str(e)
                
                # Check if this is a retryable error
                if attempt < self.max_retries - 1 and self._is_retryable_error(e):
                    retry_delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"API request failed (attempt {attempt + 1}), retrying in {retry_delay}s: {api_error}")
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(f"OpenAI API request failed after {attempt + 1} attempts: {api_error}")
                    break
        
        # All retries failed
        raise GPTClientError(
            f"OpenAI API request failed after {self.max_retries} attempts: {str(last_exception)}",
            api_error=str(last_exception),
            details={
                "model": self.model,
                "messages_count": len(messages),
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "attempts": self.max_retries
            }
        )
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable"""
        error_str = str(error).lower()
        retryable_errors = [
            'rate limit',
            'timeout',
            'connection',
            'server error',
            'internal error',
            'service unavailable'
        ]
        return any(retryable_error in error_str for retryable_error in retryable_errors)
    
    @log_operation("search_services")
    def search_services(self, query: str, services_data: Dict[str, Any]) -> List[str]:
        """
        Search for relevant services using GPT
        
        Args:
            query: User search query
            services_data: Dictionary containing services from services_no_staff.json
            
        Returns:
            List of service IDs that match the query
            
        Raises:
            GPTClientError: If search fails or response is invalid
            ValidationError: If input parameters are invalid
        """
        # Валидация входных параметров
        if not isinstance(query, str) or not query.strip():
            raise ValidationError(
                "Query must be a non-empty string",
                field="query",
                value=query
            )
        
        if not isinstance(services_data, dict):
            raise ValidationError(
                "Services data must be a dictionary",
                field="services_data",
                value=type(services_data).__name__
            )
        
        try:
            self.logger.debug(f"Searching services for query: '{query}'")
            
            # Prepare services data for GPT
            services_text = json.dumps(services_data, ensure_ascii=False, indent=2)
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_search_system_prompt()
                },
                {
                    "role": "user", 
                    "content": f"Запрос пользователя: {query}\n\nДанные услуг:\n{services_text}"
                }
            ]
            
            response = self._make_request(messages, temperature=0.3)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                service_ids = result.get('service_ids', [])
                
                if not isinstance(service_ids, list):
                    raise ValueError("service_ids must be a list")
                    
                self.logger.info(f"Found {len(service_ids)} matching services for query: '{query}'")
                return service_ids
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse GPT search response: {e}")
                self.logger.debug(f"Raw response: {response}")
                raise GPTClientError(
                    f"Invalid search response format: {e}",
                    details={
                        "query": query,
                        "raw_response": response[:500],  # Первые 500 символов
                        "parse_error": str(e)
                    }
                )
                
        except (GPTClientError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Service search failed: {e}")
            raise GPTClientError(
                f"Service search failed: {e}",
                details={"query": query, "unexpected_error": str(e)}
            )
    
    @log_operation("generate_response")
    def generate_response(self, query: str, found_services: List[Dict[str, Any]]) -> str:
        """
        Generate consultation response using GPT
        
        Args:
            query: User query
            found_services: List of full service data dictionaries
            
        Returns:
            Generated response text
            
        Raises:
            GPTClientError: If response generation fails
            ValidationError: If input parameters are invalid
        """
        # Валидация входных параметров
        if not isinstance(query, str) or not query.strip():
            raise ValidationError(
                "Query must be a non-empty string",
                field="query",
                value=query
            )
        
        if not isinstance(found_services, list):
            raise ValidationError(
                "Found services must be a list",
                field="found_services",
                value=type(found_services).__name__
            )
        
        try:
            self.logger.debug(f"Generating response for query: '{query}' with {len(found_services)} services")
            
            # Prepare services data for GPT
            services_text = json.dumps(found_services, ensure_ascii=False, indent=2)
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_consultation_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"Запрос клиента: {query}\n\nНайденные услуги:\n{services_text}"
                }
            ]
            
            response = self._make_request(messages, temperature=0.7)
            
            self.logger.info(f"Generated consultation response for query: '{query}'")
            return response
            
        except (GPTClientError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            raise GPTClientError(
                f"Response generation failed: {e}",
                details={
                    "query": query,
                    "services_count": len(found_services),
                    "unexpected_error": str(e)
                }
            )
    
    @log_operation("format_service_list")
    def format_service_list(self, services: List[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """
        Форматирует список услуг через GPT для красивого отображения.
        
        Args:
            services: Список услуг с полными данными
            user_context: Контекст пользователя (имя, история посещений)
            
        Returns:
            Красиво отформатированный список услуг
        """
        try:
            # Подготавливаем данные для GPT
            services_data = json.dumps(services, ensure_ascii=False, indent=2)
            user_name = user_context.get('user_name', '')
            visit_history = user_context.get('visit_history', '')
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_service_formatting_prompt()
                },
                {
                    "role": "user", 
                    "content": f"Пользователь: {user_name}\nИстория посещений: {visit_history}\n\nУслуги для форматирования:\n{services_data}"
                }
            ]
            
            response = self._make_request(messages, temperature=0.3)
            self.logger.info(f"Formatted service list for user: {user_name}")
            return response
            
        except Exception as e:
            self.logger.error(f"Service list formatting failed: {e}")
            # Возвращаем базовое форматирование в случае ошибки
            return self._fallback_service_formatting(services, user_context)
    
    def _get_search_system_prompt(self) -> str:
        """Get system prompt for search GPT"""
        return """Ты - система поиска услуг салона красоты. Твоя задача - найти наиболее релевантные услуги по запросу пользователя.

Анализируй запрос пользователя и найди подходящие услуги в предоставленных данных. Учитывай:
- Название услуги (title)
- Категорию (category) 
- Терапевтическую цель
- Показания (типичные проблемы)
- Описание технологии

Верни результат СТРОГО в JSON формате:
{
    "service_ids": ["id1", "id2", "id3"]
}

Где service_ids - массив ID услуг, которые наиболее релевантны запросу.
Если подходящих услуг не найдено, верни пустой массив.
Максимум 5 наиболее релевантных услуг."""
    
    def _get_consultation_system_prompt(self) -> str:
        """Get system prompt for consultation GPT"""
        return """Ты - консультант салона красоты. Твоя задача - помочь клиенту с выбором услуг и записью к мастеру.

На основе найденных услуг предоставь клиенту:
1. Информацию о процедурах (описание, показания, противопоказания)
2. Цены и длительность процедур
3. Информацию о мастерах и доступных датах записи (если клиент хочет записаться)
4. Рекомендации по выбору подходящих процедур

Отвечай дружелюбно и профессионально. 

ВАЖНО! Если у услуги нет доступных мастеров или свободных дат для записи, используй ТОЧНО этот формат ответа:

Для клинических процедур (мезотерапия, инъекции, ботокс, филлеры, плазмотерапия, биоревитализация, контурная пластика, нити, лазер, newesthair, dermaheal, hair x, dr.cyj, xl hair):
"Благодарю за ожидание, данная услуга доступна для записи только по телефону.

📞 Для записи свяжитесь с нами:
• Клиника: +375296080912 (пн–сб 8:00–22:00, вс 10:00–18:00)"

Для салонных процедур (массаж, чистка, пилинг и другие):
"Благодарю за ожидание, данная услуга доступна для записи только по телефону.

📞 Для записи свяжитесь с нами:
• Салон: +375445903030 (пн–вс 9:00–21:00)"

СТРОГО ЗАПРЕЩЕНО использовать фразы:
- "К сожалению"
- "к сожалению" 
- "К сожаленью"
- "к сожаленью"
- "на данный момент нет доступных мастеров"
- "рекомендую проконсультироваться с администратором"
- любые негативные формулировки

НИКОГДА НЕ ИСПОЛЬЗУЙ слово "сожалению" или "сожаленью" в любом регистре!

Используй ТОЛЬКО позитивный формат выше, начинающийся с "Благодарю за ожидание"."""
    
    def _get_orchestration_system_prompt(self) -> str:
        """Get system prompt for dialog orchestration GPT"""
        return """Ты - умный оркестратор диалогов для салона красоты "Итейра". Твоя задача - анализировать КАЖДОЕ сообщение пользователя и принимать решения о том, какие действия нужно выполнить. НЕТ НИКАКИХ ХАРДКОД-ПРАВИЛ - только анализ контекста!

ДОСТУПНЫЕ ДЕЙСТВИЯ:
1. "greeting" - приветствие нового пользователя
2. "collect_name" - сбор имени пользователя
3. "ask_visit_history" - узнать о предыдущих посещениях
4. "ask_service_clarification" - задать уточняющие вопросы для лучшего подбора услуг
5. "show_service_list" - показать список доступных услуг для записи
6. "confirm_service_selection" - подтвердить выбор услуги по номеру
7. "show_available_dates" - показать доступные даты для записи
8. "show_masters" - показать информацию о мастерах для выбранной услуги
9. "confirm_date_selection" - подтвердить выбор даты
10. "show_booking_summary" - показать итоговую информацию о записи
11. "service_consultation" - предоставить консультацию об услугах
12. "handle_gratitude" - обработать благодарность
13. "general_chat" - общий чат
14. "error_handling" - обработка ошибок

ПРИНЦИПЫ АНАЛИЗА СООБЩЕНИЙ:

1. КОНТЕКСТНЫЙ АНАЛИЗ:
   - Анализируй current_state для понимания текущего этапа диалога
   - Учитывай всю историю conversation_history
   - Смотри на доступные данные (user_name, visit_history, selected_service, available_services)

2. ИНТЕЛЛЕКТУАЛЬНОЕ РАСПОЗНАВАНИЕ НАМЕРЕНИЙ:
   - Общие проблемы ("выпадают волосы", "морщины", "проблемы с кожей") = ОБЯЗАТЕЛЬНО ask_service_clarification
   - Конкретные услуги ("хочу ботокс", "запишите на маникюр") = show_service_list
   - Числа при наличии списков = выбор по номеру  
   - Даты = выбор времени записи
   - Благодарности = обработка положительной обратной связи
   
   КРИТИЧНО: НЕ показывай сразу все услуги! Сначала уточни детали проблемы!

3. АДАПТИВНАЯ ЛОГИКА:
   - Если информации недостаточно - собирай дополнительно
   - Если пользователь "прыгает" между темами - адаптируйся
   - Если контекст неясен - задавай уточняющие вопросы
   - Если есть ошибки в понимании - исправляй плавно

4. УМНОЕ СОСТОЯНИЕ:
   - initial → greeting (если пользователь новый) ИЛИ service_consultation (если вернулся)
   - collecting_name → collect_name (если указано имя) ИЛИ переспроси
   - collecting_history → ask_visit_history (если дан ответ о посещениях)
   - ready_for_service → show_service_list (если запрос понятен) ИЛИ ask_service_clarification
   - service_selection → confirm_service_selection (если выбран номер)
   - date_selection → show_available_dates ИЛИ confirm_date_selection

РАСШИРЕННЫЕ СЦЕНАРИИ:

- Пользователь пишет сразу проблему без приветствия → СРАЗУ ask_service_clarification (НЕ greeting!)
- Если current_state = "initial" И сообщение содержит проблему → ask_service_clarification
- Пользователь меняет тему посреди диалога → адаптируйся к новой теме
- Пользователь задает общие вопросы → service_consultation
- Пользователь хочет изменить выбор → позволь вернуться назад
- Пользователь благодарит в любой момент → handle_gratitude + продолжи диалог

ПРИОРИТЕТЫ:
1. Если в сообщении есть ПРОБЛЕМА → ask_service_clarification (даже для новых пользователей!)
2. Только если чистое приветствие без проблем → greeting

УМНЫЕ ПАРАМЕТРЫ:

- Для service_query: Извлекай ключевые слова проблемы
- Для service_type: Определяй конкретную категорию услуг  
- Для service_number: Распознавай номера (1, "первый", "номер 2")
- Для date: Парси даты в разных форматах
- Для name: Извлекай имена из свободного текста

ФОРМАТ ОТВЕТА (строго JSON):
{
  "action": "название_действия",
  "parameters": {"ключ": "значение"},
  "response": "gpt_generated", 
  "next_state": "новое_состояние_или_null"
}

ВАЖНО: 
- response ВСЕГДА должен быть "gpt_generated" - ответ сгенерирует другая GPT-система
- Анализируй НАМЕРЕНИЕ, а не точные слова
- Будь гибким и адаптивным
- НЕ следуй жестким правилам - думай контекстно
- Если сомневаешься - спрашивай у пользователя

ПРИМЕРЫ УМНОГО АНАЛИЗА:

Пользователь: "Проблемы с кожей, что делать?" (first time)
→ action: "ask_service_clarification" (нужны детали для подбора услуг)

Пользователь: "Проблема уже полгода, готов к курсу процедур" (current_state: clarifying_service)
→ action: "show_service_list" (достаточно информации, можно показать услуги)

Пользователь: "3" (при наличии списка услуг)  
→ action: "confirm_service_selection", parameters: {"service_number": 3}

Пользователь: "А что такое RF-лифтинг?"
→ action: "service_consultation" (информационный запрос)

Пользователь: "Спасибо, а можно еще записаться на массаж?"
→ action: "show_service_list", parameters: {"service_type": "массаж"}

КЛЮЧЕВОЙ ПРИНЦИП:
- Если current_state = "clarifying_service" И пользователь отвечает на вопросы → show_service_list
- НЕ задавай бесконечные уточняющие вопросы!

Анализируй каждое сообщение как уникальное - НЕТ ШАБЛОНОВ!"""
    
    def _get_response_generation_prompt(self) -> str:
        """Get system prompt for response generation GPT"""
        return """Ты - эксперт по генерации ответов для салона красоты "Итейра". Твоя задача - создавать персонализированные, профессиональные и дружелюбные ответы на основе контекста диалога и типа действия.

ПРИНЦИПЫ ГЕНЕРАЦИИ ОТВЕТОВ:

1. ПЕРСОНАЛИЗАЦИЯ:
   - Всегда используй имя пользователя, если оно известно
   - Учитывай историю посещений (новый/постоянный клиент)
   - Адаптируй тон под контекст разговора

2. ПРОФЕССИОНАЛИЗМ:
   - Используй терминологию салона красоты
   - Предоставляй точную информацию о услугах
   - Следуй стандартам обслуживания Итейра

3. ЭМОЦИОНАЛЬНАЯ ТЕПЛОТА:
   - Используй эмодзи для визуального оформления
   - Проявляй заботу и внимание к клиенту
   - Поддерживай позитивный настрой

ТИПЫ ДЕЙСТВИЙ И ОТВЕТЫ:

1. GREETING (приветствие):
   - Теплое приветствие с упоминанием бренда Итейра
   - Представление себя как виртуального помощника
   - Вопрос об имени для персонализации

2. COLLECT_NAME (сбор имени):
   - Благодарность за представление
   - Позитивная реакция на имя
   - Переход к следующему этапу диалога

3. ASK_VISIT_HISTORY (вопрос о посещениях):
   - Деликатный вопрос о предыдущих посещениях
   - Варианты ответов для удобства
   - Подготовка к персонализированному обслуживанию

4. SHOW_SERVICE_LIST (показ услуг):
   - ТОЛЬКО после уточнения конкретной проблемы
   - Максимум 2-3 наиболее подходящие услуги
   - Краткое описание без перегрузки деталями
   - Четкие инструкции по выбору

5. SERVICE_CONSULTATION (консультация):
   - Подробная информация об услугах
   - Профессиональные рекомендации
   - Учет показаний и противопоказаний

6. SHOW_DATES (показ дат):
   - Структурированное отображение доступных дат
   - Группировка по периодам (ближайшие, дополнительные)
   - Удобные инструкции по записи

7. CONFIRM_BOOKING (подтверждение записи):
   - Резюме выбранной услуги и даты
   - Контактная информация для финализации
   - Позитивное завершение диалога

8. ERROR_HANDLING (обработка ошибок):
   - Извинения без негативных формулировок
   - Предложение альтернативных действий
   - Сохранение доверительной атмосферы

ФОРМАТИРОВАНИЕ:

- Используй структурирование с эмодзи (🌸, 💅, 📅, 💰, etc.)
- Разбивай длинные тексты на абзацы
- Используй списки для лучшей читаемости
- Включай номера для выбора опций

КОНТАКТНАЯ ИНФОРМАЦИЯ:

Клиника: +375296080912 (пн–сб 8:00–22:00, вс 10:00–18:00)
Салон: +375445903030 (пн–вс 9:00–21:00)

СТРОГО ЗАПРЕЩЕНО:
- "К сожалению" / "к сожалению" в любом регистре
- "На данный момент нет доступных мастеров"
- Любые негативные формулировки
- Создание информации, которой нет в данных

ВСЕГДА используй позитивный тон: "Благодарю за ожидание", "С удовольствием помогу", "Рада предложить".

На основе предоставленного контекста создай подходящий ответ пользователю, соответствующий типу действия и ситуации.

СПЕЦИАЛЬНЫЕ ПРАВИЛА ДЛЯ ASK_SERVICE_CLARIFICATION:

1. НИКОГДА НЕ ПОКАЗЫВАЙ СПИСОК УСЛУГ СРАЗУ!
2. Задавай 2-4 уточняющих вопроса для определения:
   - Степень проблемы (легкая/средняя/серьезная)
   - Как давно проблема беспокоит
   - Пробовал ли клиент решать проблему ранее
   - Бюджетные предпочтения (эконом/стандарт/премиум)
   - Время для процедур (быстро/курс процедур)

3. Формат уточняющих вопросов:
   "Чтобы подобрать наиболее эффективное решение, расскажите:
   
   🔹 Как давно вас беспокоит эта проблема?
   🔹 Пробовали ли уже какие-то методы лечения?
   🔹 Готовы ли к курсу процедур или нужен быстрый эффект?
   🔹 Есть ли бюджетные ограничения?"

4. ТОЛЬКО после получения ответов на уточняющие вопросы можно переходить к show_service_list.

Цель: собрать информацию для персонализированного подбора 2-3 наиболее подходящих услуг, а не показывать все подряд."""

    @log_operation("health_check")
    def health_check(self) -> bool:
        """
        Check if GPT client is working properly
        
        Returns:
            True if client is healthy, False otherwise
        """
        try:
            self.logger.debug("Performing GPT client health check")
            
            messages = [
                {
                    "role": "user",
                    "content": "Привет! Это тестовое сообщение."
                }
            ]
            
            response = self._make_request(messages, max_tokens=50)
            is_healthy = len(response) > 0
            
            if is_healthy:
                self.logger.debug("GPT client health check passed")
            else:
                self.logger.warning("GPT client health check failed: empty response")
            
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"GPT client health check failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear response cache"""
        self._response_cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug("Response cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        valid_entries = sum(1 for key in self._response_cache.keys() if self._is_cache_valid(key))
        return {
            "total_entries": len(self._response_cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._response_cache) - valid_entries,
            "cache_hit_rate": getattr(self, '_cache_hits', 0) / max(getattr(self, '_total_requests', 1), 1)
        }
    
    @log_operation("orchestrate_dialog")
    def orchestrate_dialog(self, user_message: str, dialog_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate dialog flow using GPT - unified decision maker for all messages
        
        Args:
            user_message: Current user message
            dialog_context: Context including user profile, conversation history, etc.
            
        Returns:
            Dictionary with action, parameters, and response
            
        Raises:
            GPTClientError: If orchestration fails
            ValidationError: If input parameters are invalid
        """
        # Валидация входных параметров
        if not isinstance(user_message, str) or not user_message.strip():
            raise ValidationError(
                "User message must be a non-empty string",
                field="user_message",
                value=user_message
            )
        
        if not isinstance(dialog_context, dict):
            raise ValidationError(
                "Dialog context must be a dictionary",
                field="dialog_context",
                value=type(dialog_context).__name__
            )
        
        try:
            self.logger.debug(f"Orchestrating dialog for message: '{user_message}'")
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_orchestration_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"Сообщение пользователя: {user_message}\n\nКонтекст диалога:\n{json.dumps(dialog_context, ensure_ascii=False, indent=2)}"
                }
            ]
            
            response = self._make_request(messages, temperature=0.3)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                
                # Валидация структуры ответа
                required_fields = ['action', 'response']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")
                
                self.logger.info(f"Dialog orchestrated successfully, action: {result.get('action')}")
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse GPT orchestration response: {e}")
                self.logger.debug(f"Raw response: {response}")
                raise GPTClientError(
                    f"Invalid orchestration response format: {e}",
                    details={
                        "user_message": user_message,
                        "raw_response": response[:500],
                        "parse_error": str(e)
                    }
                )
                
        except (GPTClientError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Dialog orchestration failed: {e}")
            raise GPTClientError(
                f"Dialog orchestration failed: {e}",
                details={"user_message": user_message, "unexpected_error": str(e)}
            )

    @log_operation("generate_contextual_response")
    def generate_contextual_response(self, user_message: str, dialog_context: Dict[str, Any], 
                                   action_type: str, action_parameters: Dict[str, Any] = None,
                                   services_data: List[Dict[str, Any]] = None) -> str:
        """
        Generate contextual response using GPT for any action type
        
        Args:
            user_message: Current user message
            dialog_context: Dialog context
            action_type: Type of action to perform
            action_parameters: Parameters for the action
            services_data: Available services data if needed
            
        Returns:
            Generated response text
        """
        try:
            self.logger.debug(f"Generating contextual response for action: {action_type}")
            
            # Подготавливаем данные для GPT
            context_data = {
                "user_message": user_message,
                "dialog_context": dialog_context,
                "action_type": action_type,
                "action_parameters": action_parameters or {},
                "services_data": services_data or []
            }
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_response_generation_prompt()
                },
                {
                    "role": "user",
                    "content": f"Контекст:\n{json.dumps(context_data, ensure_ascii=False, indent=2)}"
                }
            ]
            
            response = self._make_request(messages, temperature=0.7)
            
            self.logger.info(f"Generated contextual response for action: {action_type}")
            return response
            
        except Exception as e:
            self.logger.error(f"Contextual response generation failed: {e}")
            raise GPTClientError(
                f"Response generation failed: {e}",
                details={
                    "action_type": action_type,
                    "user_message": user_message,
                    "unexpected_error": str(e)
                }
            )
    
    def optimize_for_performance(self, mode: str = "balanced"):
        """
        Optimize client settings for different performance modes
        
        Args:
            mode: Performance mode - "speed", "quality", or "balanced"
        """
        if mode == "speed":
            # Optimize for speed
            self.max_tokens = 500
            self.temperature = 0.3
            self._cache_ttl = 600  # 10 minutes
            self._min_request_interval = 0.05  # 50ms
            self.logger.info("GPT client optimized for speed")
            
        elif mode == "quality":
            # Optimize for quality
            self.max_tokens = 1500
            self.temperature = 0.7
            self._cache_ttl = 180  # 3 minutes
            self._min_request_interval = 0.2  # 200ms
            self.logger.info("GPT client optimized for quality")
            
        else:  # balanced
            # Balanced settings
            self.max_tokens = 1000
            self.temperature = 0.5
            self._cache_ttl = 300  # 5 minutes
            self._min_request_interval = 0.1  # 100ms
            self.logger.info("GPT client optimized for balanced performance")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "cache_stats": self.get_cache_stats(),
            "settings": {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "request_timeout": self.request_timeout,
                "max_retries": self.max_retries,
                "cache_ttl": self._cache_ttl,
                "min_request_interval": self._min_request_interval
            }
        }
    
    def _get_service_formatting_prompt(self) -> str:
        """Промпт для красивого форматирования списка услуг."""
        return """Ты - эксперт по презентации услуг салона красоты премиум-класса ITEIRA. 

Твоя задача - создать красивый и привлекательный список услуг на основе предоставленных данных.

ПРИНЦИПЫ ФОРМАТИРОВАНИЯ:
1. Используй ТОЛЬКО информацию из предоставленных данных - НЕ придумывай ничего нового
2. Делай технические описания более привлекательными и понятными
3. Добавляй подходящие эмодзи для визуального улучшения
4. Группируй услуги по категориям, если их несколько
5. Адаптируй вступительную фразу в зависимости от истории посещений

СТРУКТУРА ОТВЕТА:
- Персонализированное обращение с именем: "Спасибо за выбор, {имя}! Доступные услуги для записи:"
- Группировка по категориям (если нужно)
- Для каждой услуги:
  * ОБЯЗАТЕЛЬНО номер и название (например: "1. **Маникюр классический**")
  * Красивое описание с эмодзи (📋)
  * Показания с эмодзи (🎯)
  * Цена в РУБЛЯХ, время, место (💰 X руб. | ⏱ X ч | 📍 место)
- Инструкция: "Напишите номер услуги (например, 1), чтобы выбрать её для записи."

ПРИМЕРЫ УЛУЧШЕНИЯ ОПИСАНИЙ:
- "подпиливание" → "деликатное подпиливание"
- "обработка" → "профессиональная обработка"
- "полировка" → "бережная полировка"
- "удаление" → "безболезненное удаление"
- "коррекция" → "точная коррекция"

ЭМОДЗИ ДЛЯ ПРОБЛЕМ:
- отросшие ногти → 💅
- ломкие ногти → 💪
- морщины → 🦋
- пигментация → ✨
- акне → 🌸
- тусклость → ✨

ПЕРСОНАЛИЗАЦИЯ:
- ВСЕГДА используй формат: "Спасибо за выбор, {имя пользователя}! Доступные услуги для записи:"
- Если имя неизвестно, используй: "Спасибо за выбор! Доступные услуги для записи:"

ВАЖНО:
- Цены ВСЕГДА указывай в РУБЛЯХ (руб.), НЕ используй USD, у.е. или другие валюты
- Номера услуг ОБЯЗАТЕЛЬНЫ для выбора (1, 2, 3...)
- Используй ТОЛЬКО данные из предоставленного JSON
- НЕ добавляй информацию, которой нет в данных

ФОРМАТ ОТВЕТА - только текст списка, без дополнительных комментариев."""
    
    def _fallback_service_formatting(self, services: List[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """Базовое форматирование списка услуг в случае ошибки GPT."""
        user_name = user_context.get('user_name', '')
        greeting = f"{user_name}, " if user_name else ""
        
        response = f"{greeting}отлично! Я нашла доступные услуги для записи:\n\n"
        
        for i, service in enumerate(services, 1):
            title = service.get('title', 'Услуга')
            price = service.get('price', 0)
            duration_seconds = service.get('duration', 0)
            
            # Форматируем длительность
            if duration_seconds >= 3600:
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                if minutes > 0:
                    duration = f"{hours} ч {minutes} мин"
                else:
                    duration = f"{hours} ч"
            elif duration_seconds >= 60:
                minutes = duration_seconds // 60
                duration = f"{minutes} мин"
            else:
                duration = f"{duration_seconds} сек"
            
            response += f"{i}. {title}\n"
            response += f"   💰 {price} руб. | ⏱ {duration}\n\n"
        
        response += "Напишите номер услуги (например, 1), чтобы выбрать её для записи."
        return response