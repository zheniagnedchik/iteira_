"""
Интеграционные тесты для RAG-системы салона красоты.
Тестируют взаимодействие между модулями и полные сценарии использования.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.modules.consultation_module import ConsultationModule
from beauty_salon_rag.modules.data_loader import DataLoader
from main import BeautySalonRAG


class TestDataFlowIntegration:
    """Тесты интеграции потока данных между модулями."""
    
    @pytest.fixture
    def test_data_files(self):
        """Создает временные файлы с тестовыми данными."""
        services_data = {
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
                    }
                ]
            }
        }
        
        services_no_staff_data = {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "massage-face-1",
                        "title": "Классический массаж лица",
                        "category": "Массаж",
                        "price": 2500,
                        "csv_fields": {
                            "Терапевтическая цель": "Омоложение и релаксация",
                            "Показания (типичные проблемы)": "Морщины, усталость кожи",
                            "Описание технологии": "Ручной массаж с использованием масел"
                        }
                    },
                    {
                        "id": "peeling-chemical-1",
                        "title": "Химический пилинг",
                        "category": "Пилинг",
                        "price": 3500,
                        "csv_fields": {
                            "Терапевтическая цель": "Обновление кожи",
                            "Показания (типичные проблемы)": "Пигментация, акне",
                            "Описание технологии": "Кислотный пилинг средней глубины"
                        }
                    }
                ]
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем файлы
            services_file = Path(temp_dir) / "services.json"
            services_no_staff_file = Path(temp_dir) / "services_no_staff.json"
            
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(services_data, f, ensure_ascii=False)
            
            with open(services_no_staff_file, 'w', encoding='utf-8') as f:
                json.dump(services_no_staff_data, f, ensure_ascii=False)
            
            yield {
                'temp_dir': temp_dir,
                'services_data': services_data,
                'services_no_staff_data': services_no_staff_data
            }
    
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    @patch('beauty_salon_rag.modules.consultation_module.GPTClient')
    def test_search_to_consultation_flow(self, mock_consultation_gpt, mock_search_gpt, test_data_files):
        """Тест полного потока от поиска к консультации."""
        # Настройка моков GPT
        mock_search_gpt_instance = Mock()
        mock_consultation_gpt_instance = Mock()
        
        mock_search_gpt.return_value = mock_search_gpt_instance
        mock_consultation_gpt.return_value = mock_consultation_gpt_instance
        
        # Поисковый GPT возвращает ID услуг
        mock_search_gpt_instance.search_services.return_value = ["massage-face-1", "peeling-chemical-1"]
        
        # Консультационный GPT возвращает ответ
        mock_consultation_gpt_instance.generate_response.return_value = (
            "Рекомендую классический массаж лица для омоложения. "
            "Доступные мастера: Анна Петрова, Мария Иванова. "
            "Цена: 2500 руб., длительность: 1 час."
        )
        
        # Создание модулей с реальными файлами
        search_module = SearchModule(test_data_files['temp_dir'])
        consultation_module = ConsultationModule(test_data_files['temp_dir'])
        
        # Выполнение поиска
        service_ids = search_module.find_services("массаж лица для омоложения")
        assert service_ids == ["massage-face-1", "peeling-chemical-1"]
        
        # Генерация консультационного ответа
        response = consultation_module.generate_consultation_response(
            "массаж лица для омоложения", service_ids
        )
        
        assert "классический массаж лица" in response.lower()
        assert "анна петрова" in response.lower()
        assert "2500" in response
        
        # Проверка вызовов GPT
        mock_search_gpt_instance.search_services.assert_called_once()
        mock_consultation_gpt_instance.generate_response.assert_called_once()
    
    def test_data_loader_integration(self, test_data_files):
        """Тест интеграции загрузчика данных с реальными файлами."""
        data_loader = DataLoader(test_data_files['temp_dir'])
        
        # Тест загрузки полных данных
        services_data = data_loader.load_services_json()
        assert services_data == test_data_files['services_data']
        
        # Тест загрузки облегченных данных
        services_no_staff_data = data_loader.load_services_no_staff_json()
        assert services_no_staff_data == test_data_files['services_no_staff_data']
        
        # Тест поиска по ID
        found_services = data_loader.get_services_by_ids(["massage-face-1"])
        assert len(found_services) == 1
        assert found_services[0]['id'] == "massage-face-1"
        assert 'companies' in found_services[0]  # Полные данные
        
        # Тест валидации существования услуги
        assert data_loader.validate_service_exists("massage-face-1") is True
        assert data_loader.validate_service_exists("nonexistent") is False
        
        # Тест получения всех ID
        all_ids = data_loader.get_all_service_ids()
        assert "massage-face-1" in all_ids
        assert "peeling-chemical-1" in all_ids
    
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    @patch('beauty_salon_rag.modules.consultation_module.GPTClient')
    def test_full_rag_system_integration(self, mock_consultation_gpt, mock_search_gpt, test_data_files):
        """Тест полной интеграции RAG-системы."""
        # Настройка моков
        mock_search_gpt_instance = Mock()
        mock_consultation_gpt_instance = Mock()
        
        mock_search_gpt.return_value = mock_search_gpt_instance
        mock_consultation_gpt.return_value = mock_consultation_gpt_instance
        
        mock_search_gpt_instance.search_services.return_value = ["massage-face-1"]
        mock_consultation_gpt_instance.generate_response.return_value = "Подробная консультация о массаже"
        
        # Создание RAG-системы
        rag_system = BeautySalonRAG(test_data_files['temp_dir'])
        
        # Тест обработки запроса
        response = rag_system.process_query("Хочу массаж лица")
        assert response == "Подробная консультация о массаже"
        
        # Тест статуса системы
        mock_search_gpt_instance.health_check.return_value = True
        mock_consultation_gpt_instance.health_check.return_value = True
        
        status = rag_system.get_system_status()
        assert status['overall_status'] is True
        assert status['search_module'] is True
        assert status['consultation_module'] is True


class TestErrorHandlingIntegration:
    """Тесты интеграции обработки ошибок."""
    
    @patch('beauty_salon_rag.modules.search_module.GPTClient')
    def test_search_module_error_propagation(self, mock_gpt):
        """Тест распространения ошибок из поискового модуля."""
        mock_gpt.side_effect = Exception("GPT initialization failed")
        
        with pytest.raises(Exception):
            SearchModule()
    
    @patch('beauty_salon_rag.modules.consultation_module.GPTClient')
    def test_consultation_module_error_propagation(self, mock_gpt):
        """Тест распространения ошибок из консультационного модуля."""
        mock_gpt.side_effect = Exception("GPT initialization failed")
        
        with pytest.raises(Exception):
            ConsultationModule()
    
    def test_missing_files_error_handling(self):
        """Тест обработки ошибок при отсутствии файлов."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_loader = DataLoader(temp_dir)
            
            # Файлы не существуют
            with pytest.raises(Exception):
                data_loader.load_services_json()
            
            with pytest.raises(Exception):
                data_loader.load_services_no_staff_json()
    
    def test_invalid_json_error_handling(self):
        """Тест обработки ошибок при некорректном JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем файл с некорректным JSON
            services_file = Path(temp_dir) / "services.json"
            with open(services_file, 'w') as f:
                f.write("invalid json content")
            
            data_loader = DataLoader(temp_dir)
            
            with pytest.raises(Exception):
                data_loader.load_services_json()


class TestPerformanceIntegration:
    """Тесты производительности интеграции."""
    
    @pytest.fixture
    def large_test_data(self):
        """Создает большой набор тестовых данных."""
        services_data = {
            "success": True,
            "data": {
                "items": []
            }
        }
        
        # Создаем 100 тестовых услуг
        for i in range(100):
            service = {
                "id": f"service-{i}",
                "title": f"Тестовая услуга {i}",
                "category": f"Категория {i % 10}",
                "price": 1000 + i * 100,
                "duration": 1800 + i * 60,
                "companies": [
                    {
                        "company_id": f"company-{i}",
                        "service_id": f"serv-{i}",
                        "staff_count": 1,
                        "staff": [
                            {
                                "id": i,
                                "name": f"Мастер {i}",
                                "booking_dates": [f"2024-01-{(i % 30) + 1:02d}"]
                            }
                        ]
                    }
                ],
                "csv_fields": {
                    "Терапевтическая цель": f"Цель {i}",
                    "Показания (типичные проблемы)": f"Проблема {i}",
                    "Описание технологии": f"Технология {i}"
                }
            }
            services_data["data"]["items"].append(service)
        
        # Создаем облегченную версию
        services_no_staff_data = {
            "success": True,
            "data": {
                "items": []
            }
        }
        
        for item in services_data["data"]["items"]:
            light_item = {
                "id": item["id"],
                "title": item["title"],
                "category": item["category"],
                "price": item["price"],
                "csv_fields": item["csv_fields"]
            }
            services_no_staff_data["data"]["items"].append(light_item)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            services_file = Path(temp_dir) / "services.json"
            services_no_staff_file = Path(temp_dir) / "services_no_staff.json"
            
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(services_data, f, ensure_ascii=False)
            
            with open(services_no_staff_file, 'w', encoding='utf-8') as f:
                json.dump(services_no_staff_data, f, ensure_ascii=False)
            
            yield temp_dir
    
    def test_large_dataset_loading_performance(self, large_test_data):
        """Тест производительности загрузки большого набора данных."""
        import time
        
        data_loader = DataLoader(large_test_data)
        
        # Измеряем время загрузки полных данных
        start_time = time.time()
        services_data = data_loader.load_services_json()
        load_time = time.time() - start_time
        
        assert len(services_data["data"]["items"]) == 100
        assert load_time < 1.0  # Должно загружаться менее чем за 1 секунду
        
        # Измеряем время повторной загрузки (из кэша)
        start_time = time.time()
        cached_data = data_loader.load_services_json()
        cache_time = time.time() - start_time
        
        assert cache_time < 0.01  # Кэш должен работать очень быстро
        assert cached_data is services_data  # Должен вернуть тот же объект
    
    def test_bulk_search_performance(self, large_test_data):
        """Тест производительности массового поиска."""
        import time
        
        data_loader = DataLoader(large_test_data)
        
        # Создаем список из 50 ID для поиска
        search_ids = [f"service-{i}" for i in range(0, 100, 2)]  # Каждый второй
        
        start_time = time.time()
        found_services = data_loader.get_services_by_ids(search_ids)
        search_time = time.time() - start_time
        
        assert len(found_services) == 50
        assert search_time < 0.5  # Поиск должен быть быстрым
        
        # Проверяем корректность результатов
        found_ids = [service["id"] for service in found_services]
        assert all(service_id in found_ids for service_id in search_ids)
    
    def test_memory_usage_with_large_dataset(self, large_test_data):
        """Тест использования памяти с большим набором данных."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Создаем несколько экземпляров загрузчика
        loaders = []
        for _ in range(5):
            loader = DataLoader(large_test_data)
            loader.load_services_json()
            loader.load_services_no_staff_json()
            loaders.append(loader)
        
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        
        # Увеличение памяти не должно быть чрезмерным (менее 50 МБ)
        assert memory_increase < 50 * 1024 * 1024
        
        # Очищаем кэши
        for loader in loaders:
            loader.clear_cache()


class TestConcurrencyIntegration:
    """Тесты параллельной работы модулей."""
    
    @pytest.fixture
    def concurrent_test_data(self):
        """Создает данные для тестов параллельности."""
        services_data = {
            "success": True,
            "data": {
                "items": [
                    {
                        "id": f"concurrent-service-{i}",
                        "title": f"Параллельная услуга {i}",
                        "category": "Тест",
                        "price": 1000,
                        "duration": 3600,
                        "companies": [],
                        "csv_fields": {}
                    }
                    for i in range(10)
                ]
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            services_file = Path(temp_dir) / "services.json"
            services_no_staff_file = Path(temp_dir) / "services_no_staff.json"
            
            with open(services_file, 'w', encoding='utf-8') as f:
                json.dump(services_data, f, ensure_ascii=False)
            
            with open(services_no_staff_file, 'w', encoding='utf-8') as f:
                json.dump(services_data, f, ensure_ascii=False)
            
            yield temp_dir
    
    def test_concurrent_data_loading(self, concurrent_test_data):
        """Тест параллельной загрузки данных."""
        import threading
        import time
        
        results = []
        errors = []
        
        def load_data():
            try:
                loader = DataLoader(concurrent_test_data)
                data = loader.load_services_json()
                results.append(len(data["data"]["items"]))
            except Exception as e:
                errors.append(e)
        
        # Создаем 10 потоков для параллельной загрузки
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=load_data)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(errors) == 0, f"Ошибки в потоках: {errors}"
        assert len(results) == 10
        assert all(result == 10 for result in results)
    
    def test_concurrent_search_operations(self, concurrent_test_data):
        """Тест параллельных операций поиска."""
        import threading
        
        data_loader = DataLoader(concurrent_test_data)
        results = []
        errors = []
        
        def search_services():
            try:
                search_ids = [f"concurrent-service-{i}" for i in range(5)]
                found = data_loader.get_services_by_ids(search_ids)
                results.append(len(found))
            except Exception as e:
                errors.append(e)
        
        # Создаем 5 потоков для параллельного поиска
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=search_services)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(errors) == 0, f"Ошибки в потоках: {errors}"
        assert len(results) == 5
        assert all(result == 5 for result in results)