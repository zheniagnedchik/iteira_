"""
Тесты для поискового модуля RAG-системы салона красоты.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from beauty_salon_rag.modules.search_module import (
    SearchModule, 
    SearchModuleError,
    search_services,
    search_services_with_details
)
from beauty_salon_rag.modules.data_loader import DataLoadError
from beauty_salon_rag.gpt_client import GPTClientError
from beauty_salon_rag.error_handler import ValidationError


class TestSearchModule:
    """Тесты для класса SearchModule."""
    
    @pytest.fixture
    def mock_services_data(self):
        """Фикстура с тестовыми данными услуг."""
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "test-id-1",
                        "title": "Массаж лица",
                        "category": "Косметология",
                        "price": 1000,
                        "csv_fields": {
                            "Терапевтическая цель": "Омоложение",
                            "Показания (типичные проблемы)": "Морщины",
                            "Описание технологии": "Ручной массаж"
                        }
                    },
                    {
                        "id": "test-id-2", 
                        "title": "Лазерная эпиляция",
                        "category": "Эпиляция",
                        "price": 500,
                        "csv_fields": {
                            "Терапевтическая цель": "Удаление волос",
                            "Показания (типичные проблемы)": "Нежелательные волосы",
                            "Описание технологии": "Лазерное воздействие"
                        }
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_data_loader(self, mock_services_data):
        """Фикстура с мок-объектом DataLoader."""
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        return mock_loader
    
    @pytest.fixture
    def mock_gpt_client(self):
        """Фикстура с мок-объектом GPTClient."""
        mock_client = Mock()
        mock_client.search_services.return_value = ["test-id-1", "test-id-2"]
        mock_client.health_check.return_value = True
        return mock_client
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_init_success(self, mock_gpt_class, mock_loader_class):
        """Тест успешной инициализации SearchModule."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        
        assert search_module.base_path == Path(".")
        mock_gpt_class.assert_called_once()
        mock_loader_class.assert_called_once_with(".")
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_init_gpt_error(self, mock_gpt_class, mock_loader_class):
        """Тест ошибки инициализации GPT клиента."""
        mock_gpt_class.side_effect = GPTClientError("API key not found")
        mock_loader_class.return_value = Mock()
        
        with pytest.raises(SearchModuleError, match="Ошибка инициализации GPT клиента"):
            SearchModule()
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_load_light_services_success(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест успешной загрузки облегченных данных."""
        mock_gpt_class.return_value = Mock()
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.load_light_services()
        
        assert result == mock_services_data
        mock_loader.load_services_no_staff_json.assert_called_once()
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_load_light_services_error(self, mock_gpt_class, mock_loader_class):
        """Тест ошибки загрузки облегченных данных."""
        mock_gpt_class.return_value = Mock()
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.side_effect = DataLoadError("File not found")
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        
        with pytest.raises(SearchModuleError, match="Ошибка загрузки облегченных данных"):
            search_module.load_light_services()
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_find_services_success(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест успешного поиска услуг."""
        mock_gpt_client = Mock()
        mock_gpt_client.search_services.return_value = ["test-id-1"]
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.find_services("массаж лица")
        
        assert result == ["test-id-1"]
        mock_gpt_client.search_services.assert_called_once_with("массаж лица", mock_services_data)
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_find_services_empty_query(self, mock_gpt_class, mock_loader_class):
        """Тест поиска с пустым запросом."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        result = search_module.find_services("")
        
        assert result == []
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_find_services_invalid_query_type(self, mock_gpt_class, mock_loader_class):
        """Тест поиска с некорректным типом запроса."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        
        with pytest.raises(ValidationError, match="Запрос должен быть строкой"):
            search_module.find_services(123)
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_find_services_gpt_error(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест ошибки GPT при поиске."""
        mock_gpt_client = Mock()
        mock_gpt_client.search_services.side_effect = GPTClientError("API error")
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        
        with pytest.raises(SearchModuleError, match="Ошибка при поиске услуг"):
            search_module.find_services("массаж")
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_validate_service_ids_success(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест успешной валидации ID услуг."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        result = search_module._validate_service_ids(
            ["test-id-1", "test-id-2"], 
            mock_services_data
        )
        
        assert result == ["test-id-1", "test-id-2"]
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_validate_service_ids_invalid_ids(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест валидации с несуществующими ID."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        result = search_module._validate_service_ids(
            ["test-id-1", "invalid-id", "test-id-2"], 
            mock_services_data
        )
        
        assert result == ["test-id-1", "test-id-2"]
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_validate_service_ids_invalid_format(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест валидации с некорректным форматом."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        result = search_module._validate_service_ids("not a list", mock_services_data)
        
        assert result == []
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_get_service_details_by_ids_success(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест успешного получения деталей услуг."""
        mock_gpt_class.return_value = Mock()
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.get_service_details_by_ids(["test-id-1"])
        
        assert len(result) == 1
        assert result[0]["id"] == "test-id-1"
        assert result[0]["title"] == "Массаж лица"
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_get_service_details_by_ids_empty_list(self, mock_gpt_class, mock_loader_class):
        """Тест получения деталей с пустым списком ID."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        result = search_module.get_service_details_by_ids([])
        
        assert result == []
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_get_service_details_by_ids_invalid_type(self, mock_gpt_class, mock_loader_class):
        """Тест получения деталей с некорректным типом."""
        mock_gpt_class.return_value = Mock()
        mock_loader_class.return_value = Mock()
        
        search_module = SearchModule()
        
        with pytest.raises(ValueError, match="service_ids должен быть списком"):
            search_module.get_service_details_by_ids("not a list")
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_search_with_details_success(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест успешного поиска с деталями."""
        mock_gpt_client = Mock()
        mock_gpt_client.search_services.return_value = ["test-id-1"]
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.search_with_details("массаж")
        
        assert len(result) == 1
        assert result[0]["id"] == "test-id-1"
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_search_with_details_no_results(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест поиска с деталями без результатов."""
        mock_gpt_client = Mock()
        mock_gpt_client.search_services.return_value = []
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.search_with_details("несуществующая услуга")
        
        assert result == []
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_health_check_success(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест успешной проверки работоспособности."""
        mock_gpt_client = Mock()
        mock_gpt_client.health_check.return_value = True
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.health_check()
        
        assert result is True
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_health_check_gpt_failure(self, mock_gpt_class, mock_loader_class, mock_services_data):
        """Тест проверки работоспособности при ошибке GPT."""
        mock_gpt_client = Mock()
        mock_gpt_client.health_check.return_value = False
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = mock_services_data
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.health_check()
        
        assert result is False
    
    @patch('beauty_salon_rag.modules.search_module.DataLoader')
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_health_check_data_failure(self, mock_gpt_class, mock_loader_class):
        """Тест проверки работоспособности при ошибке данных."""
        mock_gpt_client = Mock()
        mock_gpt_client.health_check.return_value = True
        mock_gpt_class.return_value = mock_gpt_client
        
        mock_loader = Mock()
        mock_loader.load_services_no_staff_json.return_value = {}
        mock_loader_class.return_value = mock_loader
        
        search_module = SearchModule()
        result = search_module.health_check()
        
        assert result is False


class TestSearchModuleFunctions:
    """Тесты для удобных функций модуля."""
    
    @patch('beauty_salon_rag.modules.search_module.SearchModule')
    def test_search_services_function(self, mock_search_module_class):
        """Тест функции search_services."""
        mock_instance = Mock()
        mock_instance.find_services.return_value = ["test-id-1"]
        mock_search_module_class.return_value = mock_instance
        
        result = search_services("массаж")
        
        assert result == ["test-id-1"]
        mock_search_module_class.assert_called_once_with(".")
        mock_instance.find_services.assert_called_once_with("массаж")
    
    @patch('beauty_salon_rag.modules.search_module.SearchModule')
    def test_search_services_with_details_function(self, mock_search_module_class):
        """Тест функции search_services_with_details."""
        mock_instance = Mock()
        mock_instance.search_with_details.return_value = [{"id": "test-id-1"}]
        mock_search_module_class.return_value = mock_instance
        
        result = search_services_with_details("массаж")
        
        assert result == [{"id": "test-id-1"}]
        mock_search_module_class.assert_called_once_with(".")
        mock_instance.search_with_details.assert_called_once_with("массаж")


class TestSearchModuleIntegration:
    """Интеграционные тесты для SearchModule."""
    
    @pytest.fixture
    def mock_services_data(self):
        """Фикстура с тестовыми данными услуг для интеграционных тестов."""
        return {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "test-id-1",
                        "title": "Массаж лица",
                        "category": "Косметология",
                        "price": 1000,
                        "csv_fields": {
                            "Терапевтическая цель": "Омоложение",
                            "Показания (типичные проблемы)": "Морщины",
                            "Описание технологии": "Ручной массаж"
                        }
                    }
                ]
            }
        }
    
    @pytest.fixture
    def temp_services_file(self, tmp_path, mock_services_data):
        """Создает временный файл с тестовыми данными."""
        services_file = tmp_path / "services_no_staff.json"
        with open(services_file, 'w', encoding='utf-8') as f:
            json.dump(mock_services_data, f, ensure_ascii=False)
        return str(tmp_path)
    
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_integration_search_flow(self, mock_gpt_class, temp_services_file):
        """Интеграционный тест полного цикла поиска."""
        # Настраиваем мок GPT клиента
        mock_gpt_client = Mock()
        mock_gpt_client.search_services.return_value = ["test-id-1"]
        mock_gpt_client.health_check.return_value = True
        mock_gpt_class.return_value = mock_gpt_client
        
        # Создаем поисковый модуль с реальными файлами
        search_module = SearchModule(temp_services_file)
        
        # Выполняем поиск
        result = search_module.find_services("массаж лица")
        
        # Проверяем результат
        assert result == ["test-id-1"]
        
        # Проверяем, что GPT был вызван с правильными данными
        mock_gpt_client.search_services.assert_called_once()
        call_args = mock_gpt_client.search_services.call_args
        assert call_args[0][0] == "массаж лица"  # query
        assert "data" in call_args[0][1]  # services_data
        assert "items" in call_args[0][1]["data"]