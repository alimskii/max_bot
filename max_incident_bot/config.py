import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
# Ищем .env в той же директории, где находится этот файл config.py
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Конфигурация приложения"""
    
    # MAX API настройки (токен для SDK)
    MAX_BOT_TOKEN = os.getenv('MAX_BOT_TOKEN', '').strip()
    
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
            ('MAX_BOT_TOKEN', cls.MAX_BOT_TOKEN),
            ('DIRECTUS_URL', cls.DIRECTUS_URL),
            ('DIRECTUS_TOKEN', cls.DIRECTUS_TOKEN),
            ('MAX_CHAT_ID', cls.MAX_CHAT_ID),
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            raise ValueError(f"Отсутствуют необходимые переменные окружения: {', '.join(missing)}")
        
        # Отладочный вывод (удалите после проверки)
        print(f"[DEBUG] MAX_BOT_TOKEN длина: {len(cls.MAX_BOT_TOKEN)}")
        print(f"[DEBUG] MAX_BOT_TOKEN первые 10 символов: {cls.MAX_BOT_TOKEN[:10]}...")
        
        return True
