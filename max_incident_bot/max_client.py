import requests
from typing import Dict, Any, Optional, List
from config import Config


class MAXClient:
    """Клиент для работы с MAX API"""
    
    def __init__(self):
        self.base_url = Config.MAX_API_BASE_URL
        self.token = Config.MAX_ACCESS_TOKEN
        
        self.session = requests.Session()
        # MAX API требует токен в заголовке X-Access-Token
        self.session.headers.update({
            'X-Access-Token': self.token,
            'Content-Type': 'application/json'
        })
    
    def send_message(self, chat_id: str, text: str, 
                     format_type: str = 'markdown',
                     disable_link_preview: bool = False,
                     notify: bool = True) -> Optional[Dict[str, Any]]:
        """
        Отправляет сообщение в чат
        
        Args:
            chat_id: ID чата для отправки сообщения
            text: Текст сообщения (до 4000 символов)
            format_type: Форматирование ('markdown' или 'html')
            disable_link_preview: Не генерировать превью для ссылок
            notify: Уведомлять участников чата
            
        Returns:
            Данные отправленного сообщения или None
        """
        url = f"{self.base_url}/messages"
        
        params = {
            'chat_id': chat_id
        }
        
        payload = {
            'text': text,
            'format': format_type,
            'disable_link_preview': disable_link_preview,
            'notify': notify
        }
        
        try:
            response = self.session.post(url, params=params, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('message')
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке сообщения: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            return None
    
    def send_message_to_user(self, user_id: str, text: str,
                            format_type: str = 'markdown') -> Optional[Dict[str, Any]]:
        """
        Отправляет сообщение пользователю
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            format_type: Форматирование ('markdown' или 'html')
            
        Returns:
            Данные отправленного сообщения или None
        """
        url = f"{self.base_url}/messages"
        
        params = {
            'user_id': user_id
        }
        
        payload = {
            'text': text,
            'format': format_type
        }
        
        try:
            response = self.session.post(url, params=params, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('message')
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке сообщения пользователю: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            return None
    
    def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о чате
        
        Args:
            chat_id: ID чата
            
        Returns:
            Информация о чате или None
        """
        url = f"{self.base_url}/chats/{chat_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении информации о чате: {e}")
            return None
