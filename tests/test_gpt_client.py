"""
Тесты для GPT клиента RAG-системы салона красоты.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.error_handler import GPTClientError, ConfigurationError, ValidationError


class TestGPTClient:
    """Test cases for GPTClient class"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client"""
        with patch('beauty_salon_rag.gpt_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def gpt_client(self, mock_openai_client):
        """Create GPTClient instance with mocked OpenAI"""
        with patch('beauty_salon_rag.gpt_client.config') as mock_config:
            mock_config.get_openai_key.return_value = "test_key"
            mock_config.get_openai_config.return_value = {
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7
            }
            return GPTClient()
    
    def test_init_success(self, mock_openai_client):
        """Test successful GPT client initialization"""
        with patch('beauty_salon_rag.gpt_client.config') as mock_config:
            mock_config.get_openai_key.return_value = "test_key"
            mock_config.get_openai_config.return_value = {
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7
            }
            
            client = GPTClient()
            assert client.model == 'gpt-3.5-turbo'
            assert client.max_tokens == 1000
            assert client.temperature == 0.7
    
    def test_init_no_api_key(self, mock_openai_client):
        """Test GPT client initialization without API key"""
        with patch('beauty_salon_rag.gpt_client.config') as mock_config:
            mock_config.get_openai_key.side_effect = ValueError("API key not found")
            
            with pytest.raises(ConfigurationError):
                GPTClient()
    
    def test_make_request_success(self, gpt_client, mock_openai_client):
        """Test successful API request"""
        # Mock response
        mock_message = ChatCompletionMessage(role="assistant", content="Test response")
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion"
        )
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test message"}]
        result = gpt_client._make_request(messages)
        
        assert result == "Test response"
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_make_request_empty_response(self, gpt_client, mock_openai_client):
        """Test API request with empty response"""
        mock_message = ChatCompletionMessage(role="assistant", content=None)
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion"
        )
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test message"}]
        
        with pytest.raises(GPTClientError, match="Empty response"):
            gpt_client._make_request(messages)
    
    def test_search_services_success(self, gpt_client, mock_openai_client):
        """Test successful service search"""
        # Mock GPT response
        search_response = json.dumps({"service_ids": ["service1", "service2"]})
        mock_message = ChatCompletionMessage(role="assistant", content=search_response)
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion"
        )
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        services_data = {"services": [{"id": "service1", "title": "Test Service"}]}
        result = gpt_client.search_services("массаж", services_data)
        
        assert result == ["service1", "service2"]
    
    def test_search_services_invalid_json(self, gpt_client, mock_openai_client):
        """Test service search with invalid JSON response"""
        mock_message = ChatCompletionMessage(role="assistant", content="Invalid JSON")
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion"
        )
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        services_data = {"services": []}
        
        with pytest.raises(GPTClientError, match="Invalid search response format"):
            gpt_client.search_services("массаж", services_data)
    
    def test_generate_response_success(self, gpt_client, mock_openai_client):
        """Test successful response generation"""
        consultation_response = "Рекомендую массаж лица для улучшения состояния кожи."
        mock_message = ChatCompletionMessage(role="assistant", content=consultation_response)
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion"
        )
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        found_services = [{"id": "service1", "title": "Массаж лица", "price": 2000}]
        result = gpt_client.generate_response("Хочу улучшить состояние кожи", found_services)
        
        assert result == consultation_response
    
    def test_health_check_success(self, gpt_client, mock_openai_client):
        """Test successful health check"""
        mock_message = ChatCompletionMessage(role="assistant", content="Привет!")
        mock_choice = Choice(index=0, message=mock_message, finish_reason="stop")
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=1234567890,
            model="gpt-3.5-turbo",
            object="chat.completion"
        )
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = gpt_client.health_check()
        assert result is True
    
    def test_health_check_failure(self, gpt_client, mock_openai_client):
        """Test health check failure"""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = gpt_client.health_check()
        assert result is False