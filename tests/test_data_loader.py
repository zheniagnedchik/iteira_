"""
Тесты для модуля data_loader.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from beauty_salon_rag.modules.data_loader import (
    DataLoader, 
    DataLoadError,
    load_services,
    load_services_no_staff,
    find_services_by_ids
)


class TestDataLoader(unittest.TestCase):
    """Тесты для класса DataLoader."""
    
    def setUp(self):
        """Подготовка тестовых данных."""
        self.test_services_data = {
            "success": True,
            "message": "Test data",
            "data": {
                "limit": 10,
                "count": 2,
                "total_documents": 2,
                "items": [
                    {
                        "title": "Тест услуга 1",
                        "price": 1000,
                        "category": "Тестовая категория",
                        "id": "test-id-1",
                        "duration": 3600,
                        "staff": [{"id": 1, "name": "Мастер 1"}],
                        "companies": [{"company_id": "123", "staff": []}],
                        "csv_fields": {"Описание": "Тестовое описание 1"}
                    },
                    {
                        "title": "Тест услуга 2", 
                        "price": 2000,
                        "category": "Тестовая категория 2",
                        "id": "test-id-2",
                        "duration": 1800,
                        "staff": [{"id": 2, "name": "Мастер 2"}],
                        "companies": [{"company_id": "456", "staff": []}],
                        "csv_fields": {"Описание": "Тестовое описание 2"}
                    }
                ]
            }
        }
        
        self.test_services_no_staff_data = {
            "success": True,
            "message": "Test data without staff",
            "data": {
                "limit": 10,
                "count": 2,
                "total_documents": 2,
                "items": [
                    {
                        "title": "Тест услуга 1",
                        "price": 1000,
                        "category": "Тестовая категория",
                        "id": "test-id-1",
                        "duration": 3600,
                        "companies": [{"company_id": "123", "staff": []}],
                        "csv_fields": {"Описание": "Тестовое описание 1"}
                    },
                    {
                        "title": "Тест услуга 2",
                        "price": 2000,
                        "category": "Тестовая категория 2", 
                        "id": "test-id-2",
                        "duration": 1800,
                        "companies": [{"company_id": "456", "staff": []}],
                        "csv_fields": {"Описание": "Тестовое описание 2"}
                    }
                ]
            }
        }
    
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
            self.assertEqual(len(data['data']['items']), 2)
    
    def test_load_services_no_staff_json_success(self):
        """Тест успешной загрузки services_no_staff.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый файл
            services_file = Path(temp_dir) / "services_no_staff.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_services_no_staff_data, f)
            
            # Тестируем загрузку
            loader = DataLoader(temp_dir)
            data = loader.load_services_no_staff_json()
            
            self.assertEqual(data, self.test_services_no_staff_data)
            self.assertEqual(len(data['data']['items']), 2)
    
    def test_load_services_json_file_not_found(self):
        """Тест обработки отсутствующего файла services.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = DataLoader(temp_dir)
            
            with self.assertRaises(DataLoadError) as context:
                loader.load_services_json()
            
            self.assertIn("не найден", str(context.exception))
    
    def test_load_services_json_invalid_json(self):
        """Тест обработки некорректного JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем файл с некорректным JSON
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                f.write("invalid json content")
            
            loader = DataLoader(temp_dir)
            
            with self.assertRaises(DataLoadError) as context:
                loader.load_services_json()
            
            self.assertIn("Ошибка парсинга JSON", str(context.exception))
    
    def test_load_services_json_invalid_structure(self):
        """Тест обработки некорректной структуры данных."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем файл с некорректной структурой
            invalid_data = {"wrong": "structure"}
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(invalid_data, f)
            
            loader = DataLoader(temp_dir)
            
            with self.assertRaises(DataLoadError) as context:
                loader.load_services_json()
            
            self.assertIn("Некорректная структура данных", str(context.exception))


class TestServiceSearch(unittest.TestCase):
    """Тесты для функций поиска услуг."""
    
    def setUp(self):
        """Подготовка тестовых данных."""
        self.test_data = {
            "success": True,
            "message": "Test data",
            "data": {
                "items": [
                    {"id": "service-1", "title": "Услуга 1", "price": 1000},
                    {"id": "service-2", "title": "Услуга 2", "price": 2000},
                    {"id": "service-3", "title": "Услуга 3", "price": 3000}
                ]
            }
        }
    
    def test_get_services_by_ids_success(self):
        """Тест успешного поиска услуг по ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый файл
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_data, f)
            
            loader = DataLoader(temp_dir)
            
            # Тестируем поиск существующих услуг
            found_services = loader.get_services_by_ids(["service-1", "service-3"])
            
            self.assertEqual(len(found_services), 2)
            self.assertEqual(found_services[0]["id"], "service-1")
            self.assertEqual(found_services[1]["id"], "service-3")
    
    def test_get_services_by_ids_partial_found(self):
        """Тест поиска услуг когда найдены не все ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_data, f)
            
            loader = DataLoader(temp_dir)
            
            # Тестируем поиск с несуществующими ID
            found_services = loader.get_services_by_ids(["service-1", "nonexistent-id"])
            
            self.assertEqual(len(found_services), 1)
            self.assertEqual(found_services[0]["id"], "service-1")
    
    def test_get_services_by_ids_empty_list(self):
        """Тест поиска с пустым списком ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_data, f)
            
            loader = DataLoader(temp_dir)
            found_services = loader.get_services_by_ids([])
            
            self.assertEqual(len(found_services), 0)
    
    def test_get_services_by_ids_invalid_input(self):
        """Тест обработки некорректных входных данных."""
        from beauty_salon_rag.error_handler import ValidationError
        loader = DataLoader()
        
        with self.assertRaises(ValidationError):
            loader.get_services_by_ids("not-a-list")
    
    def test_validate_service_exists(self):
        """Тест валидации существования услуги."""
        with tempfile.TemporaryDirectory() as temp_dir:
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_data, f)
            
            loader = DataLoader(temp_dir)
            
            # Тестируем существующую услугу
            self.assertTrue(loader.validate_service_exists("service-1"))
            
            # Тестируем несуществующую услугу
            self.assertFalse(loader.validate_service_exists("nonexistent"))
            
            # Тестируем некорректный тип
            self.assertFalse(loader.validate_service_exists(123))
    
    def test_get_all_service_ids(self):
        """Тест получения всех ID услуг."""
        with tempfile.TemporaryDirectory() as temp_dir:
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_data, f)
            
            loader = DataLoader(temp_dir)
            service_ids = loader.get_all_service_ids()
            
            expected_ids = ["service-1", "service-2", "service-3"]
            self.assertEqual(sorted(service_ids), sorted(expected_ids))


class TestConvenienceFunctions(unittest.TestCase):
    """Тесты для удобных функций быстрого доступа."""
    
    @patch('beauty_salon_rag.modules.data_loader.DataLoader')
    def test_load_services(self, mock_loader_class):
        """Тест функции load_services."""
        mock_loader = mock_loader_class.return_value
        mock_loader.load_services_json.return_value = {"test": "data"}
        
        result = load_services()
        
        mock_loader_class.assert_called_once()
        mock_loader.load_services_json.assert_called_once()
        self.assertEqual(result, {"test": "data"})
    
    @patch('beauty_salon_rag.modules.data_loader.DataLoader')
    def test_load_services_no_staff(self, mock_loader_class):
        """Тест функции load_services_no_staff."""
        mock_loader = mock_loader_class.return_value
        mock_loader.load_services_no_staff_json.return_value = {"test": "data"}
        
        result = load_services_no_staff()
        
        mock_loader_class.assert_called_once()
        mock_loader.load_services_no_staff_json.assert_called_once()
        self.assertEqual(result, {"test": "data"})
    
    @patch('beauty_salon_rag.modules.data_loader.DataLoader')
    def test_find_services_by_ids(self, mock_loader_class):
        """Тест функции find_services_by_ids."""
        mock_loader = mock_loader_class.return_value
        mock_loader.get_services_by_ids.return_value = [{"id": "test"}]
        
        result = find_services_by_ids(["test-id"])
        
        mock_loader_class.assert_called_once()
        mock_loader.get_services_by_ids.assert_called_once_with(["test-id"])
        self.assertEqual(result, [{"id": "test"}])


if __name__ == '__main__':
    unittest.main()