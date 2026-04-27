import requests
from typing import List, Dict, Any, Optional
from config import Config


class DirectusClient:
    """Клиент для работы с Directus API"""
    
    def __init__(self):
        self.base_url = Config.DIRECTUS_URL.rstrip('/')
        self.token = Config.DIRECTUS_TOKEN
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })
    
    def get_incidents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает список заявок из коллекции asudd_incidents
        
        Args:
            limit: Максимальное количество записей для получения
            
        Returns:
            Список заявок
        """
        url = f"{self.base_url}/items/{Config.INCIDENTS_COLLECTION}"
        
        params = {
            'limit': limit,
            'sort': '-date_created',  # Сортировка по дате создания (новые сначала)
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении заявок из Directus: {e}")
            return []
    
    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает заявку по ID
        
        Args:
            incident_id: ID заявки
            
        Returns:
            Данные заявки или None
        """
        url = f"{self.base_url}/items/{Config.INCIDENTS_COLLECTION}/{incident_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data')
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении заявки {incident_id}: {e}")
            return None
    
    def update_incident(self, incident_id: str, data: Dict[str, Any]) -> bool:
        """
        Обновляет заявку
        
        Args:
            incident_id: ID заявки
            data: Данные для обновления
            
        Returns:
            True если успешно, иначе False
        """
        url = f"{self.base_url}/items/{Config.INCIDENTS_COLLECTION}/{incident_id}"
        
        try:
            response = self.session.patch(url, json=data)
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при обновлении заявки {incident_id}: {e}")
            return False
    
    def download_image(self, image_url: str) -> Optional[bytes]:
        """
        Скачивает изображение по URL из Directus
        
        Args:
            image_url: URL изображения
            
        Returns:
            Байты изображения или None
        """
        try:
            response = self.session.get(image_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при скачивании изображения {image_url}: {e}")
            return None
    
    def get_asset_url(self, image_id: str) -> str:
        """
        Получает URL изображения из Directus assets
        
        Args:
            image_id: UUID изображения в Directus
            
        Returns:
            Полный URL изображения
        """
        return f"{self.base_url}/assets/{image_id}"
