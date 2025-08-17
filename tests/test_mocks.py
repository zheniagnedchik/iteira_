"""
Модуль с мок-объектами и фикстурами для тестирования RAG-системы салона красоты.
"""

import json
from unittest.mock import Mock, MagicMock
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage


class MockGPTClient:
    """Мок-класс для GPT клиента с предустановленными ответами."""
    
    def __init__(self):
        self.search_responses = {
            "массаж лица": ["massage-face-1", "massage-face-2"],
            "пилинг": ["peeling-chemical-1", "peeling-mechanical-1"],
            "чистка": ["cleaning-ultrasonic-1", "cleaning-manual-1"],
            "омоложение": ["massage-face-1", "peeling-chemical-1", "rf-lifting-1"],
            "акне": ["peeling-chemical-1", "cleaning-ultrasonic-1"],
            "морщины": ["massage-face-1", "rf-lifting-1", "botox-1"]
        }
        
        self.consultation_responses = {
            "массаж лица": (
                "Рекомендую классический массаж лица для омоложения и релаксации. "
                "Процедура поможет улучшить кровообращение, разгладить мелкие морщины "
                "и придать коже здоровый вид. Доступные мастера: Анна Петрова, Мария Иванова. "
                "Цена: 2500 руб., длительность: 1 час."
            ),
            "пилинг": (
                "Химический пилинг эффективно обновляет кожу, устраняет пигментацию "
                "и следы от акне. Процедура требует реабилитации 3-5 дней. "
                "Доступный мастер: Елена Сидорова. Цена: 3500 руб., длительность: 45 мин."
            ),
            "чистка": (
                "Ультразвуковая чистка лица мягко очищает поры и удаляет загрязнения. "
                "Подходит для всех типов кожи. Рекомендуется проводить раз в месяц. "
                "Цена: 2000 руб., длительность: 1 час."
            )
        }
    
    def search_services(self, query: str, services_data: dict) -> list:
        """Мок-метод поиска услуг."""
        query_lower = query.lower()
        
        # Ищем подходящий ответ по ключевым словам
        for keyword, service_ids in self.search_responses.items():
            if keyword in query_lower:
                return service_ids
        
        # Если не найдено, возвращаем пустой список
        return []
    
    def generate_response(self, query: str, found_services: list) -> str:
        """Мок-метод генерации ответа."""
        query_lower = query.lower()
        
        # Ищем подходящий ответ по ключевым словам
        for keyword, response in self.consultation_responses.items():
            if keyword in query_lower:
                return response
        
        # Общий ответ если не найдено специфичного
        if found_services:
            service_titles = [service.get('title', 'Услуга') for service in found_services]
            return f"Найдены следующие услуги: {', '.join(service_titles)}. Обратитесь к администратору для записи."
        else:
            return "К сожалению, подходящие услуги не найдены. Обратитесь к администратору."
    
    def health_check(self) -> bool:
        """Мок-метод проверки здоровья."""
        return True


def create_mock_openai_response(content: str) -> ChatCompletion:
    """Создает мок-ответ от OpenAI API."""
    mock_message = ChatCompletionMessage(role="assistant", content=content)
    mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
    
    return ChatCompletion(
        id="test_completion_id",
        choices=[mock_choice],
        created=1234567890,
        model="gpt-3.5-turbo",
        object="chat.completion"
    )


def create_mock_search_response(service_ids: list) -> str:
    """Создает мок-ответ для поиска услуг."""
    return json.dumps({"service_ids": service_ids})


def create_test_services_data():
    """Создает тестовые данные услуг."""
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": "massage-face-1",
                    "title": "Классический массаж лица",
                    "category": "Массаж",
                    "price": 2500,
                    "duration": 3600,
                    "companies": [
                        {
                            "company_id": "salon-1",
                            "service_id": "serv-1",
                            "staff_count": 2,
                            "staff": [
                                {
                                    "id": 1,
                                    "name": "Анна Петрова",
                                    "booking_dates": ["2024-01-15", "2024-01-16"]
                                },
                                {
                                    "id": 2,
                                    "name": "Мария Иванова",
                                    "booking_dates": ["2024-01-17", "2024-01-18"]
                                }
                            ]
                        }
                    ],
                    "csv_fields": {
                        "Терапевтическая цель": "Омоложение и релаксация",
                        "Показания (типичные проблемы)": "Морщины, усталость кожи",
                        "Противопоказания (стандартные + уточнения)": "Воспаления кожи",
                        "Описание технологии": "Ручной массаж с использованием масел",
                        "Детали": "Включает очищение и увлажнение",
                        "Место оказания услуг": "салон"
                    }
                },
                {
                    "id": "peeling-chemical-1",
                    "title": "Химический пилинг",
                    "category": "Пилинг",
                    "price": 3500,
                    "duration": 2700,
                    "companies": [
                        {
                            "company_id": "salon-1",
                            "service_id": "serv-2",
                            "staff_count": 1,
                            "staff": [
                                {
                                    "id": 3,
                                    "name": "Елена Сидорова",
                                    "booking_dates": ["2024-01-20", "2024-01-21"]
                                }
                            ]
                        }
                    ],
                    "csv_fields": {
                        "Терапевтическая цель": "Обновление кожи",
                        "Показания (типичные проблемы)": "Пигментация, акне",
                        "Противопоказания (стандартные + уточнения)": "Беременность, чувствительная кожа",
                        "Описание технологии": "Кислотный пилинг средней глубины",
                        "Детали": "Требует реабилитации 3-5 дней",
                        "Место оказания услуг": "клиника"
                    }
                },
                {
                    "id": "cleaning-ultrasonic-1",
                    "title": "Ультразвуковая чистка лица",
                    "category": "Чистка",
                    "price": 2000,
                    "duration": 3600,
                    "companies": [
                        {
                            "company_id": "salon-2",
                            "service_id": "serv-3",
                            "staff_count": 3,
                            "staff": [
                                {
                                    "id": 4,
                                    "name": "Ольга Козлова",
                                    "booking_dates": ["2024-01-22", "2024-01-23"]
                                },
                                {
                                    "id": 5,
                                    "name": "Татьяна Морозова",
                                    "booking_dates": ["2024-01-24", "2024-01-25"]
                                }
                            ]
                        }
                    ],
                    "csv_fields": {
                        "Терапевтическая цель": "Глубокое очищение",
                        "Показания (типичные проблемы)": "Черные точки, расширенные поры",
                        "Противопоказания (стандартные + уточнения)": "Острые воспаления",
                        "Описание технологии": "Ультразвуковые волны для очищения",
                        "Детали": "Безболезненная процедура",
                        "Место оказания услуг": "салон"
                    }
                }
            ]
        }
    }


def create_test_services_no_staff_data():
    """Создает тестовые данные услуг без персонала."""
    full_data = create_test_services_data()
    
    # Удаляем информацию о персонале
    no_staff_data = {
        "success": True,
        "data": {
            "items": []
        }
    }
    
    for item in full_data["data"]["items"]:
        no_staff_item = {
            "id": item["id"],
            "title": item["title"],
            "category": item["category"],
            "price": item["price"],
            "csv_fields": item["csv_fields"]
        }
        no_staff_data["data"]["items"].append(no_staff_item)
    
    return no_staff_data


class MockDataLoader:
    """Мок-класс для загрузчика данных."""
    
    def __init__(self, base_path="."):
        self.base_path = base_path
        self._services_data = create_test_services_data()
        self._services_no_staff_data = create_test_services_no_staff_data()
    
    def load_services_json(self):
        return self._services_data
    
    def load_services_no_staff_json(self):
        return self._services_no_staff_data
    
    def get_services_by_ids(self, service_ids):
        items = self._services_data["data"]["items"]
        return [item for item in items if item["id"] in service_ids]
    
    def validate_service_exists(self, service_id):
        items = self._services_data["data"]["items"]
        return any(item["id"] == service_id for item in items)
    
    def get_all_service_ids(self):
        items = self._services_data["data"]["items"]
        return [item["id"] for item in items]


class MockSearchModule:
    """Мок-класс для поискового модуля."""
    
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.gpt_client = MockGPTClient()
        self.data_loader = MockDataLoader(base_path)
    
    def find_services(self, query):
        services_data = self.data_loader.load_services_no_staff_json()
        return self.gpt_client.search_services(query, services_data)
    
    def search_with_details(self, query):
        service_ids = self.find_services(query)
        return self.data_loader.get_services_by_ids(service_ids)
    
    def health_check(self):
        return True


class MockConsultationModule:
    """Мок-класс для консультационного модуля."""
    
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.gpt_client = MockGPTClient()
        self.data_loader = MockDataLoader(base_path)
    
    def generate_consultation_response(self, query, service_ids):
        services = self.data_loader.get_services_by_ids(service_ids)
        return self.gpt_client.generate_response(query, services)
    
    def get_services_by_ids(self, service_ids):
        return self.data_loader.get_services_by_ids(service_ids)
    
    def health_check(self):
        return True


def create_mock_config():
    """Создает мок-конфигурацию."""
    mock_config = Mock()
    mock_config.get_openai_key.return_value = "test_api_key"
    mock_config.get_openai_config.return_value = {
        'model': 'gpt-3.5-turbo',
        'max_tokens': 1000,
        'temperature': 0.7
    }
    return mock_config


def create_realistic_gpt_responses():
    """Создает реалистичные ответы GPT для различных запросов."""
    return {
        "search_responses": {
            "массаж лица омоложение": json.dumps({"service_ids": ["massage-face-1"]}),
            "пилинг акне пигментация": json.dumps({"service_ids": ["peeling-chemical-1"]}),
            "чистка лица поры": json.dumps({"service_ids": ["cleaning-ultrasonic-1"]}),
            "процедуры для лица": json.dumps({"service_ids": ["massage-face-1", "peeling-chemical-1", "cleaning-ultrasonic-1"]}),
            "несуществующая процедура": json.dumps({"service_ids": []})
        },
        "consultation_responses": {
            "массаж лица": (
                "Классический массаж лица - отличный выбор для омоложения и релаксации! "
                "Эта процедура поможет:\n\n"
                "✨ Улучшить кровообращение и лимфодренаж\n"
                "✨ Разгладить мелкие морщины\n"
                "✨ Повысить тонус и эластичность кожи\n"
                "✨ Снять напряжение лицевых мышц\n\n"
                "💰 Стоимость: 2500 руб.\n"
                "⏰ Длительность: 1 час\n"
                "📍 Место проведения: салон\n\n"
                "👩‍⚕️ Доступные мастера:\n"
                "• Анна Петрова - свободна 15, 16 января\n"
                "• Мария Иванова - свободна 17, 18 января\n\n"
                "Процедура включает очищение и увлажнение кожи. "
                "Противопоказания: воспаления кожи."
            ),
            "пилинг": (
                "Химический пилинг - эффективная процедура для обновления кожи! "
                "Рекомендуется при:\n\n"
                "🎯 Пигментации и постакне\n"
                "🎯 Неровном рельефе кожи\n"
                "🎯 Расширенных порах\n"
                "🎯 Тусклом цвете лица\n\n"
                "💰 Стоимость: 3500 руб.\n"
                "⏰ Длительность: 45 минут\n"
                "📍 Место проведения: клиника\n\n"
                "👩‍⚕️ Мастер: Елена Сидорова\n"
                "📅 Свободные даты: 20, 21 января\n\n"
                "⚠️ Важно: процедура требует реабилитации 3-5 дней. "
                "Противопоказания: беременность, чувствительная кожа."
            )
        }
    }