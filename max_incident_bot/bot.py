#!/usr/bin/env python3
"""
MAX Incident Bot

Бот для отправки сообщений из Directus в групповой чат MAX.
Мониторит коллекцию asudd_incidents и отправляет уведомления о новых заявках.
Использует официальный SDK maxapi для работы с мессенджером MAX.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Set
from datetime import datetime

from config import Config
from directus_client import DirectusClient
from maxapi import Bot

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
        self.bot_token = Config.MAX_BOT_TOKEN
        # MAX API требует int для chat_id, но у нас строка - нужно извлечь ID
        # Chat ID в формате MAX может быть строкой, но send_message принимает int или None
        # Попробуем использовать как есть (строку), так как API MAX поддерживает строковые ID
        self.chat_id_str = Config.MAX_CHAT_ID
        self.processed_incidents: Set[str] = set()
        
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
        incident_number = incident.get('incident_number', 'Не указан')
        status = incident.get('status', 'Не указан')
        dispatcher_name = incident.get('dispatcher_name', 'Не указан')
        request_at = incident.get('request_at', 'Не указано')
        date_created = incident.get('date_created', 'Не указано')
        sent_to_work_at = incident.get('sent_to_work_at', 'Не отправлено')
        completed_at = incident.get('completed_at', 'Не завершена')
        
        # Формируем сообщение с Markdown форматированием
        message = f"""🚨 *Заявка #{incident_id}*

*Номер заявки:* {incident_number}
*Статус:* {status}
*Диспетчер:* {dispatcher_name}

*Дата создания:* {date_created}
*Время запроса:* {request_at}
*Отправлено в работу:* {sent_to_work_at}
*Завершена:* {completed_at}

---
_Заявка создана в Directus_"""
        
        return message
    
    async def send_incident_notification(self, bot: Bot, incident: Dict[str, Any]) -> bool:
        """
        Отправляет уведомление о заявке в групповой чат
        
        Args:
            bot: Экземпляр бота MAX
            incident: Данные заявки
            
        Returns:
            True если успешно отправлено
        """
        message = self.format_incident_message(incident)
        
        try:
            # MAX API send_message принимает chat_id как int или None
            # Для строковых ID используем параметр text и передаём chat_id напрямую
            await bot.send_message(
                chat_id=self.chat_id_str,
                text=message,
            )
            logger.info(f"Сообщение о заявке #{incident.get('id')} отправлено в чат")
            return True
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение о заявке #{incident.get('id')}: {e}")
            return False
    
    def mark_as_sent(self, incident_id: str):
        """
        Помечает заявку как отправленную
        
        Args:
            incident_id: ID заявки
        """
        self.processed_incidents.add(incident_id)
    
    async def check_new_incidents(self, bot: Bot) -> int:
        """
        Проверяет наличие новых заявок и отправляет уведомления
        
        Args:
            bot: Экземпляр бота MAX
            
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
            if await self.send_incident_notification(bot, incident):
                self.mark_as_sent(incident_id)
                new_count += 1
        
        if new_count > 0:
            logger.info(f"Обработано новых заявок: {new_count}")
        
        return new_count
    
    async def run(self):
        """Запускает основной цикл работы бота"""
        logger.info("Запуск бота...")
        logger.info(f"Интервал опроса: {Config.POLLING_INTERVAL} сек.")
        logger.info(f"Чат для уведомлений: {self.chat_id}")
        
        bot = Bot(self.bot_token)
        
        # Удаляем существующие вебхуки для использования polling
        try:
            await bot.delete_webhook()
            logger.info("Вебхук удалён для использования polling режима")
        except Exception as e:
            logger.warning(f"Не удалось удалить вебхук: {e}")
        
        try:
            while True:
                start_time = time.time()
                
                try:
                    await self.check_new_incidents(bot)
                except Exception as e:
                    logger.error(f"Ошибка при проверке заявок: {e}")
                
                # Вычисляем время сна, чтобы интервал был стабильным
                elapsed = time.time() - start_time
                sleep_time = max(0, Config.POLLING_INTERVAL - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            raise


async def main():
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
    await bot.run()
    
    return 0


if __name__ == '__main__':
    exit(asyncio.run(main()))
