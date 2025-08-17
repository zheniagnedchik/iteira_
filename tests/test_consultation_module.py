"""
Тесты для консультационного модуля RAG-системы салона красоты.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from beauty_salon_rag.modules.consultation_module import (
    ConsultationModule,
    ConsultationModuleError,
    get_consultation_response,
    get_services_with_staff_info
)
from beauty_salon_rag.modules.data_loader import DataLoadError
from beauty_salon_rag.gpt_client import GPTClientError
from beauty_salon_rag.error_handler import ValidationError


class TestConsultationModule:
    """Тесты для класса ConsultationModule."""
    
    @pytest.fixture
    def mock_services_data(self):
        """Фикстура с тестовыми данными услуг."""
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "test-id-1",
                        "title": "Тестовая процедура 1",
                        "category": "Тестовая категория",
                        "price": 1000,
                        "duration": 3600,
                        "companies": [
                            {
                                "company_id": "comp-1",
                                "service_id": "serv-1",
                                "staff_count": 2,
                                "staff": [
                                    {
                                        "id": 1,
                                        "name": "Мастер Иван",
                                        "booking_dates": ["2024-01-15", "2024-01-16"]
                                    },
                                    {
                                        "id": 2,
                                        "name": "Мастер Анна",
                                        "booking_dates": ["2024-01-17", "2024-01-18"]
                                    }
                                ]
                            }
                        ],
                        "csv_fields": {
                            "Терапевтическая цель": "Омоложение",
                            "Показания (типичные проблемы)": "Морщины, дряблость",
                            "Противопоказания (стандартные + уточнения)": "Беременность",
                            "Описание технологии": "Лазерная технология",
                            "Детали": "Включает консультацию",
                            "Место оказания услуг": "клиника"
                        }
                    },
                    {
                        "id": "test-id-2",
                        "title": "Тестовая процедура 2",
                        "category": "Другая категория",
                        "price": 500,
                        "duration": 1800,
                        "companies": [],
                        "csv_fields": {}
                    }
                ]
            }
        }
    
    @pytest.fixture
    def consultation_module(self):
        """Фикстура с консультационным модулем."""
        with patch('beauty_salon_rag.modules.consultation_module.GPTClient'):
            return ConsultationModule()
    
    def test_init_success(self):
        """Тест успешной инициализации модуля."""
        with patch('beauty_salon_rag.modules.consultation_module.GPTClient') as mock_gpt:
            module = ConsultationModule()
            assert module.base_path == Path(".")
            assert module.data_loader is not None
            mock_gpt.assert_called_once()
    
    def test_init_gpt_error(self):
        """Тест ошибки инициализации GPT клиента."""
        with patch('beauty_salon_rag.modules.consultation_module.GPTClient', 
                  side_effect=GPTClientError("GPT error")):
            with pytest.raises(ConsultationModuleError, match="Ошибка инициализации GPT клиента"):
                ConsultationModule()
    
    def test_load_full_services_success(self, consultation_module, mock_services_data):
        """Тест успешной загрузки полных данных услуг."""
        consultation_module.data_loader.load_services_json = Mock(return_value=mock_services_data)
        
        result = consultation_module.load_full_services()
        
        assert result == mock_services_data
        consultation_module.data_loader.load_services_json.assert_called_once()
    
    def test_load_full_services_error(self, consultation_module):
        """Тест ошибки загрузки полных данных услуг."""
        consultation_module.data_loader.load_services_json = Mock(
            side_effect=DataLoadError("Load error")
        )
        
        with pytest.raises(ConsultationModuleError, match="Ошибка загрузки полных данных"):
            consultation_module.load_full_services()
    
    def test_get_services_by_ids_success(self, consultation_module, mock_services_data):
        """Тест успешного получения услуг по ID."""
        expected_services = mock_services_data["data"]["items"]
        consultation_module.data_loader.get_services_by_ids = Mock(return_value=expected_services)
        
        result = consultation_module.get_services_by_ids(["test-id-1", "test-id-2"])
        
        assert result == expected_services
        consultation_module.data_loader.get_services_by_ids.assert_called_once_with(["test-id-1", "test-id-2"])
    
    def test_get_services_by_ids_invalid_input(self, consultation_module):
        """Тест некорректных входных параметров для получения услуг по ID."""
        with pytest.raises(ValueError, match="service_ids должен быть списком"):
            consultation_module.get_services_by_ids("not-a-list")
    
    def test_get_services_by_ids_empty_list(self, consultation_module):
        """Тест пустого списка ID услуг."""
        result = consultation_module.get_services_by_ids([])
        assert result == []
    
    def test_get_services_by_ids_data_error(self, consultation_module):
        """Тест ошибки загрузки данных при получении услуг по ID."""
        consultation_module.data_loader.get_services_by_ids = Mock(
            side_effect=DataLoadError("Data error")
        )
        
        with pytest.raises(ConsultationModuleError, match="Ошибка получения услуг по ID"):
            consultation_module.get_services_by_ids(["test-id-1"])
    
    def test_format_staff_info_with_staff(self, consultation_module):
        """Тест форматирования информации о мастерах."""
        service = {
            "id": "test-id",
            "companies": [
                {
                    "company_id": "comp-1",
                    "service_id": "serv-1", 
                    "staff_count": 2,
                    "staff": [
                        {
                            "id": 1,
                            "name": "Мастер Иван",
                            "booking_dates": ["2024-01-15", "2024-01-16"]
                        },
                        {
                            "id": 2,
                            "name": "Мастер Анна", 
                            "booking_dates": ["2024-01-17"]
                        }
                    ]
                }
            ]
        }
        
        result = consultation_module.format_staff_info(service)
        
        assert result["total_staff_count"] == 2
        assert len(result["available_masters"]) == 2
        assert len(result["companies"]) == 1
        
        master1 = result["available_masters"][0]
        assert master1["name"] == "Мастер Иван"
        assert master1["booking_dates"] == ["2024-01-15", "2024-01-16"]
    
    def test_format_staff_info_no_companies(self, consultation_module):
        """Тест форматирования информации о мастерах без компаний."""
        service = {"id": "test-id", "companies": []}
        
        result = consultation_module.format_staff_info(service)
        
        assert result["total_staff_count"] == 0
        assert result["available_masters"] == []
        assert result["companies"] == []
    
    def test_format_duration(self, consultation_module):
        """Тест форматирования длительности процедуры."""
        # Тест секунд
        assert consultation_module._format_duration(30) == "30 сек"
        
        # Тест минут
        assert consultation_module._format_duration(120) == "2 мин"
        
        # Тест часов
        assert consultation_module._format_duration(3600) == "1 ч"
        
        # Тест часов и минут
        assert consultation_module._format_duration(3900) == "1 ч 5 мин"
        
        # Тест None
        assert consultation_module._format_duration(None) == "Не указано"
        
        # Тест некорректного типа
        assert consultation_module._format_duration("invalid") == "Не указано"
    
    def test_format_service_details(self, consultation_module, mock_services_data):
        """Тест форматирования деталей услуги."""
        service = mock_services_data["data"]["items"][0]
        
        result = consultation_module.format_service_details(service)
        
        assert result["id"] == "test-id-1"
        assert result["title"] == "Тестовая процедура 1"
        assert result["price"] == 1000
        assert result["duration"] == 3600
        assert result["duration_formatted"] == "1 ч"
        assert result["therapeutic_goal"] == "Омоложение"
        assert result["indications"] == "Морщины, дряблость"
        assert "staff_info" in result
    
    def test_generate_consultation_response_success(self, consultation_module, mock_services_data):
        """Тест успешной генерации консультационного ответа."""
        services = mock_services_data["data"]["items"]
        consultation_module.get_services_by_ids = Mock(return_value=services)
        consultation_module.gpt_client.generate_response = Mock(return_value="Тестовый ответ")
        
        result = consultation_module.generate_consultation_response("тест запрос", ["test-id-1"])
        
        assert result == "Тестовый ответ"
        consultation_module.get_services_by_ids.assert_called_once_with(["test-id-1"])
        consultation_module.gpt_client.generate_response.assert_called_once()
    
    def test_generate_consultation_response_invalid_query(self, consultation_module):
        """Тест некорректного запроса для генерации ответа."""
        with pytest.raises(ValidationError, match="Запрос должен быть непустой строкой"):
            consultation_module.generate_consultation_response("", ["test-id-1"])
        
        with pytest.raises(ValidationError, match="Запрос должен быть непустой строкой"):
            consultation_module.generate_consultation_response(None, ["test-id-1"])
    
    def test_generate_consultation_response_invalid_service_ids(self, consultation_module):
        """Тест некорректных ID услуг для генерации ответа."""
        with pytest.raises(ValidationError, match="service_ids должен быть списком"):
            consultation_module.generate_consultation_response("тест", "not-a-list")
    
    def test_generate_consultation_response_no_services(self, consultation_module):
        """Тест генерации ответа когда услуги не найдены."""
        consultation_module.get_services_by_ids = Mock(return_value=[])
        
        result = consultation_module.generate_consultation_response("тест запрос", ["test-id-1"])
        
        assert "не найдено подходящих услуг" in result
        assert "тест запрос" in result
    
    def test_generate_consultation_response_gpt_error(self, consultation_module, mock_services_data):
        """Тест ошибки GPT при генерации ответа."""
        services = mock_services_data["data"]["items"]
        consultation_module.get_services_by_ids = Mock(return_value=services)
        consultation_module.gpt_client.generate_response = Mock(
            side_effect=GPTClientError("GPT error")
        )
        
        with pytest.raises(ConsultationModuleError, match="Ошибка при генерации ответа"):
            consultation_module.generate_consultation_response("тест запрос", ["test-id-1"])
    
    def test_get_booking_info_success(self, consultation_module, mock_services_data):
        """Тест успешного получения информации о записи."""
        services = mock_services_data["data"]["items"]
        consultation_module.get_services_by_ids = Mock(return_value=services)
        
        result = consultation_module.get_booking_info(["test-id-1", "test-id-2"])
        
        assert result["total_services"] == 2
        assert len(result["services"]) == 2
        assert len(result["all_masters"]) == 2  # Два мастера из первой услуги
        
        service_booking = result["services"][0]
        assert service_booking["service_id"] == "test-id-1"
        assert service_booking["service_title"] == "Тестовая процедура 1"
        assert service_booking["price"] == 1000
    
    def test_get_booking_info_error(self, consultation_module):
        """Тест ошибки получения информации о записи."""
        consultation_module.get_services_by_ids = Mock(
            side_effect=Exception("Test error")
        )
        
        with pytest.raises(ConsultationModuleError, match="Ошибка получения информации о записи"):
            consultation_module.get_booking_info(["test-id-1"])
    
    def test_health_check_success(self, consultation_module, mock_services_data):
        """Тест успешной проверки работоспособности."""
        consultation_module.load_full_services = Mock(return_value=mock_services_data)
        consultation_module.gpt_client.health_check = Mock(return_value=True)
        
        result = consultation_module.health_check()
        
        assert result is True
    
    def test_health_check_no_data(self, consultation_module):
        """Тест проверки работоспособности без данных."""
        consultation_module.load_full_services = Mock(return_value={})
        
        result = consultation_module.health_check()
        
        assert result is False
    
    def test_health_check_gpt_error(self, consultation_module, mock_services_data):
        """Тест проверки работоспособности с ошибкой GPT."""
        consultation_module.load_full_services = Mock(return_value=mock_services_data)
        consultation_module.gpt_client.health_check = Mock(return_value=False)
        
        result = consultation_module.health_check()
        
        assert result is False
    
    def test_health_check_exception(self, consultation_module):
        """Тест проверки работоспособности с исключением."""
        consultation_module.load_full_services = Mock(side_effect=Exception("Test error"))
        
        result = consultation_module.health_check()
        
        assert result is False


class TestConsultationModuleFunctions:
    """Тесты для удобных функций модуля."""
    
    @patch('beauty_salon_rag.modules.consultation_module.ConsultationModule')
    def test_get_consultation_response(self, mock_consultation_class):
        """Тест функции быстрого получения консультационного ответа."""
        mock_module = Mock()
        mock_module.generate_consultation_response.return_value = "Тестовый ответ"
        mock_consultation_class.return_value = mock_module
        
        result = get_consultation_response("тест запрос", ["test-id-1"], "/test/path")
        
        assert result == "Тестовый ответ"
        mock_consultation_class.assert_called_once_with("/test/path")
        mock_module.generate_consultation_response.assert_called_once_with("тест запрос", ["test-id-1"])
    
    @patch('beauty_salon_rag.modules.consultation_module.ConsultationModule')
    def test_get_services_with_staff_info(self, mock_consultation_class):
        """Тест функции быстрого получения услуг с информацией о мастерах."""
        mock_module = Mock()
        mock_services = [{"id": "test-id-1"}]
        mock_formatted = [{"id": "test-id-1", "formatted": True}]
        
        mock_module.get_services_by_ids.return_value = mock_services
        mock_module.format_service_details.return_value = mock_formatted[0]
        mock_consultation_class.return_value = mock_module
        
        result = get_services_with_staff_info(["test-id-1"], "/test/path")
        
        assert result == mock_formatted
        mock_consultation_class.assert_called_once_with("/test/path")
        mock_module.get_services_by_ids.assert_called_once_with(["test-id-1"])


class TestConsultationModuleIntegration:
    """Интеграционные тесты для консультационного модуля."""
    
    @pytest.fixture
    def mock_services_data(self):
        """Фикстура с тестовыми данными услуг для интеграционных тестов."""
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "test-id-1",
                        "title": "Тестовая процедура 1",
                        "category": "Тестовая категория",
                        "price": 1000,
                        "duration": 3600,
                        "companies": [
                            {
                                "company_id": "comp-1",
                                "service_id": "serv-1",
                                "staff_count": 2,
                                "staff": [
                                    {
                                        "id": 1,
                                        "name": "Мастер Иван",
                                        "booking_dates": ["2024-01-15", "2024-01-16"]
                                    },
                                    {
                                        "id": 2,
                                        "name": "Мастер Анна",
                                        "booking_dates": ["2024-01-17", "2024-01-18"]
                                    }
                                ]
                            }
                        ],
                        "csv_fields": {
                            "Терапевтическая цель": "Омоложение",
                            "Показания (типичные проблемы)": "Морщины, дряблость",
                            "Противопоказания (стандартные + уточнения)": "Беременность",
                            "Описание технологии": "Лазерная технология",
                            "Детали": "Включает консультацию",
                            "Место оказания услуг": "клиника"
                        }
                    }
                ]
            }
        }
    
    @pytest.fixture
    def temp_services_file(self, tmp_path, mock_services_data):
        """Создает временный файл services.json для тестов."""
        services_file = tmp_path / "services.json"
        with open(services_file, 'w', encoding='utf-8') as f:
            json.dump(mock_services_data, f, ensure_ascii=False)
        return str(tmp_path)
    
    @patch('beauty_salon_rag.modules.consultation_module.GPTClient')
    def test_full_workflow(self, mock_gpt_class, temp_services_file, mock_services_data):
        """Тест полного рабочего процесса консультационного модуля."""
        # Настройка мока GPT
        mock_gpt = Mock()
        mock_gpt.generate_response.return_value = "Консультационный ответ"
        mock_gpt.health_check.return_value = True
        mock_gpt_class.return_value = mock_gpt
        
        # Создание модуля
        module = ConsultationModule(temp_services_file)
        
        # Тест загрузки данных
        services_data = module.load_full_services()
        assert services_data == mock_services_data
        
        # Тест получения услуг по ID
        services = module.get_services_by_ids(["test-id-1"])
        assert len(services) == 1
        assert services[0]["id"] == "test-id-1"
        
        # Тест форматирования деталей услуги
        formatted = module.format_service_details(services[0])
        assert formatted["id"] == "test-id-1"
        assert formatted["title"] == "Тестовая процедура 1"
        assert "staff_info" in formatted
        
        # Тест генерации ответа
        response = module.generate_consultation_response("тест запрос", ["test-id-1"])
        assert response == "Консультационный ответ"
        
        # Тест проверки работоспособности
        assert module.health_check() is True