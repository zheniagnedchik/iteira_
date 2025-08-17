"""
Тесты для модуля конфигурации RAG-системы салона красоты.
"""

import os
import pytest
from unittest.mock import patch, Mock

from beauty_salon_rag.config import Config, config, load_config


class TestConfig:
    """Тесты для класса Config."""
    
    def test_init_default_config(self):
        """Тест инициализации с конфигурацией по умолчанию."""
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            
            # Проверяем структуру конфигурации
            assert 'openai' in test_config._config
            assert 'data' in test_config._config
            assert 'logging' in test_config._config
            assert 'app' in test_config._config
    
    def test_init_with_env_vars(self):
        """Тест инициализации с переменными окружения."""
        env_vars = {
            'OPENAI_API_KEY': 'test_key_123',
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_MAX_TOKENS': '2000',
            'OPENAI_TEMPERATURE': '0.5',
            'SERVICES_FILE': 'custom_services.json',
            'SERVICES_NO_STAFF_FILE': 'custom_no_staff.json',
            'LOG_LEVEL': 'DEBUG',
            'DEBUG': 'true'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Config()
            
            # Проверяем OpenAI настройки
            assert test_config._config['openai']['api_key'] == 'test_key_123'
            assert test_config._config['openai']['model'] == 'gpt-4'
            assert test_config._config['openai']['max_tokens'] == 2000
            assert test_config._config['openai']['temperature'] == 0.5
            
            # Проверяем файлы данных
            assert test_config._config['data']['services_file'] == 'custom_services.json'
            assert test_config._config['data']['services_no_staff_file'] == 'custom_no_staff.json'
            
            # Проверяем логирование
            assert test_config._config['logging']['level'] == 'DEBUG'
            
            # Проверяем приложение
            assert test_config._config['app']['debug'] is True
    
    def test_get_existing_key(self):
        """Тест получения существующего ключа."""
        with patch.dict(os.environ, {'OPENAI_MODEL': 'gpt-4'}, clear=True):
            test_config = Config()
            
            # Простой ключ
            assert test_config.get('openai') is not None
            
            # Вложенный ключ
            assert test_config.get('openai.model') == 'gpt-4'
            assert test_config.get('openai.max_tokens') == 1000  # значение по умолчанию
    
    def test_get_nonexistent_key(self):
        """Тест получения несуществующего ключа."""
        test_config = Config()
        
        # Несуществующий ключ без значения по умолчанию
        assert test_config.get('nonexistent.key') is None
        
        # Несуществующий ключ со значением по умолчанию
        assert test_config.get('nonexistent.key', 'default') == 'default'
    
    def test_get_invalid_key_path(self):
        """Тест получения ключа с некорректным путем."""
        test_config = Config()
        
        # Попытка получить ключ из не-словаря
        assert test_config.get('openai.model.invalid') is None
        assert test_config.get('openai.model.invalid', 'default') == 'default'
    
    def test_get_openai_key_success(self):
        """Тест успешного получения OpenAI API ключа."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key_123'}, clear=True):
            test_config = Config()
            
            api_key = test_config.get_openai_key()
            assert api_key == 'test_key_123'
    
    def test_get_openai_key_missing(self):
        """Тест получения OpenAI API ключа когда он отсутствует."""
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                test_config.get_openai_key()
    
    def test_get_openai_config(self):
        """Тест получения конфигурации OpenAI."""
        env_vars = {
            'OPENAI_API_KEY': 'test_key',
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_MAX_TOKENS': '1500',
            'OPENAI_TEMPERATURE': '0.3'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Config()
            
            openai_config = test_config.get_openai_config()
            
            assert openai_config['api_key'] == 'test_key'
            assert openai_config['model'] == 'gpt-4'
            assert openai_config['max_tokens'] == 1500
            assert openai_config['temperature'] == 0.3
    
    def test_get_data_files(self):
        """Тест получения путей к файлам данных."""
        env_vars = {
            'SERVICES_FILE': 'test_services.json',
            'SERVICES_NO_STAFF_FILE': 'test_no_staff.json'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Config()
            
            data_files = test_config.get_data_files()
            
            assert data_files['services_file'] == 'test_services.json'
            assert data_files['services_no_staff_file'] == 'test_no_staff.json'
    
    def test_invalid_numeric_env_vars(self):
        """Тест обработки некорректных числовых переменных окружения."""
        env_vars = {
            'OPENAI_MAX_TOKENS': 'not_a_number',
            'OPENAI_TEMPERATURE': 'invalid_float'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Должно вызвать исключение при попытке преобразования
            with pytest.raises(ValueError):
                Config()
    
    def test_debug_flag_variations(self):
        """Тест различных вариантов флага отладки."""
        # Тест true
        with patch.dict(os.environ, {'DEBUG': 'true'}, clear=True):
            test_config = Config()
            assert test_config._config['app']['debug'] is True
        
        # Тест True
        with patch.dict(os.environ, {'DEBUG': 'True'}, clear=True):
            test_config = Config()
            assert test_config._config['app']['debug'] is True
        
        # Тест TRUE
        with patch.dict(os.environ, {'DEBUG': 'TRUE'}, clear=True):
            test_config = Config()
            assert test_config._config['app']['debug'] is True
        
        # Тест false
        with patch.dict(os.environ, {'DEBUG': 'false'}, clear=True):
            test_config = Config()
            assert test_config._config['app']['debug'] is False
        
        # Тест любого другого значения
        with patch.dict(os.environ, {'DEBUG': 'anything'}, clear=True):
            test_config = Config()
            assert test_config._config['app']['debug'] is False


class TestGlobalConfig:
    """Тесты для глобального экземпляра конфигурации."""
    
    def test_global_config_instance(self):
        """Тест глобального экземпляра конфигурации."""
        # Проверяем, что config является экземпляром Config
        assert isinstance(config, Config)
        
        # Проверяем, что у него есть необходимые методы
        assert hasattr(config, 'get')
        assert hasattr(config, 'get_openai_key')
        assert hasattr(config, 'get_openai_config')
        assert hasattr(config, 'get_data_files')
    
    def test_load_config_function(self):
        """Тест функции load_config."""
        loaded_config = load_config()
        
        # Проверяем, что возвращается тот же экземпляр
        assert loaded_config is config
        assert isinstance(loaded_config, Config)


class TestConfigIntegration:
    """Интеграционные тесты для конфигурации."""
    
    def test_dotenv_loading(self):
        """Тест загрузки переменных из .env файла."""
        # Проверяем, что модуль импортируется без ошибок
        # load_dotenv вызывается при импорте модуля
        import beauty_salon_rag.config
        
        # Проверяем, что конфигурация создается корректно
        assert hasattr(beauty_salon_rag.config, 'config')
        assert isinstance(beauty_salon_rag.config.config, beauty_salon_rag.config.Config)
    
    def test_config_with_real_env_file(self):
        """Тест конфигурации с реальными переменными окружения."""
        # Сохраняем текущие переменные
        original_env = dict(os.environ)
        
        try:
            # Устанавливаем тестовые переменные
            os.environ.update({
                'OPENAI_API_KEY': 'sk-test123',
                'OPENAI_MODEL': 'gpt-3.5-turbo',
                'LOG_LEVEL': 'INFO'
            })
            
            # Создаем новый экземпляр конфигурации
            test_config = Config()
            
            # Проверяем, что значения загружены корректно
            assert test_config.get('openai.api_key') == 'sk-test123'
            assert test_config.get('openai.model') == 'gpt-3.5-turbo'
            assert test_config.get('logging.level') == 'INFO'
            
        finally:
            # Восстанавливаем исходные переменные
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_config_defaults_when_no_env(self):
        """Тест значений по умолчанию когда переменные окружения отсутствуют."""
        with patch.dict(os.environ, {}, clear=True):
            test_config = Config()
            
            # Проверяем значения по умолчанию
            assert test_config.get('openai.model') == 'gpt-3.5-turbo'
            assert test_config.get('openai.max_tokens') == 1000
            assert test_config.get('openai.temperature') == 0.7
            assert test_config.get('data.services_file') == 'services.json'
            assert test_config.get('data.services_no_staff_file') == 'services_no_staff.json'
            assert test_config.get('logging.level') == 'INFO'
            assert test_config.get('app.debug') is False