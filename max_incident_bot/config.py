import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # MAX API настройки
    MAX_ACCESS_TOKEN = os.getenv('MAX_ACCESS_TOKEN', '').strip()
    MAX_API_BASE_URL = 'https://platform-api.max.ru'
    
    # Directus настройки
    DIRECTUS_URL = os.getenv('DIRECTUS_URL', '').strip().rstrip('/')
    DIRECTUS_TOKEN = os.getenv('DIRECTUS_TOKEN', '').strip()
    
    # ID группового чата для отправки сообщений
    MAX_CHAT_ID = os.getenv('MAX_CHAT_ID', '').strip()
    
    # Интервал опроса Directus (в секундах)
    POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '10'))
    
    # Коллекция Directus с заявками
    INCIDENTS_COLLECTION = 'asudd_incidents'
    
    @classmethod
    def validate(cls):
        """Проверяет наличие всех необходимых настроек"""
        required_vars = [
            ('MAX_ACCESS_TOKEN', cls.MAX_ACCESS_TOKEN),
            ('DIRECTUS_URL', cls.DIRECTUS_URL),
            ('DIRECTUS_TOKEN', cls.DIRECTUS_TOKEN),
            ('MAX_CHAT_ID', cls.MAX_CHAT_ID),
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            raise ValueError(f"Отсутствуют необходимые переменные окружения: {', '.join(missing)}")
        
        # Отладочный вывод (удалите после проверки)
        print(f"[DEBUG] MAX_ACCESS_TOKEN длина: {len(cls.MAX_ACCESS_TOKEN)}")
        print(f"[DEBUG] MAX_ACCESS_TOKEN первые 10 символов: {cls.MAX_ACCESS_TOKEN[:10]}...")
        
        return True
