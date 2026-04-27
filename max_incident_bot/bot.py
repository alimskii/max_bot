#!/usr/bin/env python3
"""
MAX Incident Bot

Бот для отправки сообщений из Directus в групповой чат MAX.
Мониторит коллекцию asudd_incidents и отправляет уведомления о новых заявках.
"""

import time
import logging
from typing import Dict, Any, Set, List
from datetime import datetime

from config import Config
from directus_client import DirectusClient
from max_client import MAXClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class IncidentBot:
    """Основной класс бота для обработки заявок"""
    
    def __init__(self):
        self.directus = DirectusClient()
        self.max_client = MAXClient()
        self.processed_incidents: Set[str] = set()
        self.chat_id = Config.MAX_CHAT_ID
        
    def format_incident_message(self, incident: Dict[str, Any]) -> str:
        """
        Форматирует заявку в сообщение для отправки в MAX
        
        Args:
            incident: Данные заявки из Directus
            
        Returns:
            Отформатированное сообщение
        """
        # Получаем поля заявки (адаптируйте под вашу структуру коллекции)
        incident_id = incident.get('id', 'Не указан')
        title = incident.get('title', incident.get('name', 'Без названия'))
        description = incident.get('description', incident.get('text', 'Нет описания'))
        status = incident.get('status', 'Не указан')
        priority = incident.get('priority', 'Не указана')
        created_at = incident.get('date_created', incident.get('created_at', 'Не указано'))
        
        # Формируем сообщение с Markdown форматированием
        message = f"""🚨 *Новая заявка #{incident_id}*

*Заголовок:* {title}

*Описание:*
{description}

*Статус:* {status}
*Приоритет:* {priority}
*Дата создания:* {created_at}

---
_Заявка создана в Directus_"""
        
        return message
    
    def send_incident_notification(self, incident: Dict[str, Any]) -> bool:
        """
        Отправляет уведомление о заявке в групповой чат
        
        Args:
            incident: Данные заявки
            
        Returns:
            True если успешно отправлено
        """
        message = self.format_incident_message(incident)
        
        result = self.max_client.send_message(
            chat_id=self.chat_id,
            text=message,
            format_type='markdown',
            notify=True
        )
        
        if result:
            logger.info(f"Сообщение о заявке #{incident.get('id')} отправлено в чат")
            return True
        else:
            logger.error(f"Не удалось отправить сообщение о заявке #{incident.get('id')}")
            return False
    
    def mark_as_sent(self, incident_id: str):
        """
        Помечает заявку как отправленную
        
        Args:
            incident_id: ID заявки
        """
        self.processed_incidents.add(incident_id)
        
        # Опционально: можно обновлять статус в Directus
        # self.directus.update_incident(incident_id, {'sent_to_max': True})
    
    def check_new_incidents(self) -> int:
        """
        Проверяет наличие новых заявок и отправляет уведомления
        
        Returns:
            Количество обработанных заявок
        """
        incidents = self.directus.get_incidents(limit=50)
        
        if not incidents:
            logger.debug("Новых заявок не найдено")
            return 0
        
        new_count = 0
        
        for incident in incidents:
            incident_id = str(incident.get('id'))
            
            # Пропускаем уже обработанные заявки
            if incident_id in self.processed_incidents:
                continue
            
            # Отправляем уведомление
            if self.send_incident_notification(incident):
                self.mark_as_sent(incident_id)
                new_count += 1
        
        if new_count > 0:
            logger.info(f"Обработано новых заявок: {new_count}")
        
        return new_count
    
    def run(self):
        """Запускает основной цикл работы бота"""
        logger.info("Запуск бота...")
        logger.info(f"Интервал опроса: {Config.POLLING_INTERVAL} сек.")
        logger.info(f"Чат для уведомлений: {self.chat_id}")
        
        try:
            while True:
                start_time = time.time()
                
                try:
                    self.check_new_incidents()
                except Exception as e:
                    logger.error(f"Ошибка при проверке заявок: {e}")
                
                # Вычисляем время сна, чтобы интервал был стабильным
                elapsed = time.time() - start_time
                sleep_time = max(0, Config.POLLING_INTERVAL - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            raise


def main():
    """Точка входа приложения"""
    
    # Валидация конфигурации
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        logger.error("Проверьте файл .env или переменные окружения")
        return 1
    
    # Создание и запуск бота
    bot = IncidentBot()
    bot.run()
    
    return 0


if __name__ == '__main__':
    exit(main())
