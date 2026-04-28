#!/usr/bin/env python3
"""
MAX Incident Bot

Бот для отправки сообщений из Directus в групповой чат MAX.
Мониторит коллекцию asudd_incidents и отправляет уведомления о новых заявках.
Использует официальный SDK maxapi для работы с мессенджером MAX.
Поддерживает отправку изображений вместе с текстовым сообщением.
"""

import asyncio
import time
import logging
import tempfile
import os
from typing import Dict, Any, Set, Optional, List
from datetime import datetime, timezone
import locale

from config import Config
from directus_client import DirectusClient
from maxapi import Bot
from maxapi.types import InputMedia
from maxapi.enums.upload_type import UploadType

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def format_date_ru(date_string: str) -> str:
    """
    Преобразует дату из формата ISO 8601 в читаемый русский формат.
    
    Args:
        date_string: Дата в формате ISO 8601 (например, "2026-04-22T13:09:23.000Z")
        
    Returns:
        Дата в русском формате (например, "22 апреля 2026 г. 13:09")
    """
    if not date_string or date_string == 'Не указано':
        return 'Не указано'
    
    try:
        from datetime import timedelta
        
        # Парсим дату из ISO 8601
        # Убираем миллисекунды и Z, если есть
        date_string_clean = date_string.replace('Z', '+00:00')
        
        # Пробуем распарсить с разными форматами
        dt = datetime.fromisoformat(date_string_clean)
        
        # Конвертируем в московское время (UTC+3)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)
        
        # Форматируем на русском языке
        month_names = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        
        day = dt.day
        month = month_names[dt.month]
        year = dt.year
        hour = dt.hour
        minute = dt.minute
        
        result = f"{day} {month} {year} г. {hour:02d}:{minute:02d}"
        logger.debug(f"Преобразование даты: '{date_string}' -> '{result}'")
        return result
        
    except Exception as e:
        logger.warning(f"Не удалось преобразовать дату '{date_string}': {e}")
        return date_string


class IncidentBot:
    """Основной класс бота для обработки заявок"""
    
    def __init__(self):
        self.directus = DirectusClient()
        self.bot_token = Config.MAX_BOT_TOKEN
        # Chat ID в формате MAX - строка, но SDK требует int или None
        # Сохраняем как есть, преобразование попробуем позже
        self.chat_id_str: str = Config.MAX_CHAT_ID
        self.chat_id_int: Optional[int] = None
        self.processed_incidents: Set[str] = set()
        
        # Пробуем преобразовать chat_id в int, если это возможно
        try:
            self.chat_id_int = int(self.chat_id_str)
            logger.debug(f"Chat ID преобразован в int: {self.chat_id_int}")
        except (ValueError, TypeError):
            logger.debug(f"Chat ID не является числом, используем как строку: {self.chat_id_str}")
    
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
        engineer_id = incident.get('engineer_id', 'Не указан')
        
        # Форматируем даты в читаемый русский формат
        request_at_raw = incident.get('request_at', 'Не указано')
        date_created_raw = incident.get('date_created', 'Не указано')
        sent_to_work_at_raw = incident.get('sent_to_work_at', 'Не отправлено')
        completed_at_raw = incident.get('completed_at', 'Не завершена')
        
        request_at = format_date_ru(request_at_raw) if request_at_raw else 'Не указано'
        date_created = format_date_ru(date_created_raw) if date_created_raw else 'Не указано'
        sent_to_work_at = format_date_ru(sent_to_work_at_raw) if sent_to_work_at_raw else 'Не отправлено'
        completed_at = format_date_ru(completed_at_raw) if completed_at_raw else 'Не завершена'
        
        # Формируем сообщение с Markdown форматированием
        message = f"""🚨 Заявка {incident_id}

Номер заявки: {incident_number}
Статус: {status}
Диспетчер: {dispatcher_name}
Инженер: {engineer_id}

Дата создания: {date_created}
Время запроса: {request_at}
Отправлено в работу: {sent_to_work_at}
Завершена: {completed_at}

"""
        
        return message
    
    async def send_incident_notification(self, bot: Bot, incident: Dict[str, Any]) -> bool:
        """
        Отправляет уведомление о заявке в групповой чат (с изображением или без)
        
        Args:
            bot: Экземпляр бота MAX
            incident: Данные заявки
            
        Returns:
            True если успешно отправлено
        """
        message = self.format_incident_message(incident)
        
        # Проверяем наличие изображения в заявке
        image_id = incident.get('incidents_photo')
        attachments: List[InputMedia] = []
        tmp_path = None
        
        if image_id:
            logger.info(f"Заявка #{incident.get('id')} имеет изображение: {image_id}")
            try:
                # Получаем URL изображения из Directus
                image_url = self.directus.get_asset_url(image_id)
                logger.info(f"Попытка загрузить изображение: {image_url}")
                
                # Скачиваем изображение
                image_data = self.directus.download_image(image_url)
                
                if image_data:
                    logger.info(f"Изображение загружено, размер: {len(image_data)} байт")
                    # Создаем временный файл для изображения
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(image_data)
                        tmp_path = tmp_file.name
                    
                    logger.info(f"Временный файл создан: {tmp_path}")
                    
                    try:
                        # Создаем InputMedia для изображения
                        media = InputMedia(path=tmp_path, type=UploadType.IMAGE)
                        attachments.append(media)
                        logger.info(f"Изображение подготовлено для отправки")
                    except Exception as e:
                        logger.error(f"Ошибка при создании InputMedia: {e}", exc_info=True)
                        # Удаляем временный файл при ошибке
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            tmp_path = None
                        raise
                else:
                    logger.warning(f"Не удалось загрузить данные изображения")
            except Exception as e:
                logger.warning(f"Не удалось загрузить изображение для заявки #{incident.get('id')}: {e}", exc_info=True)
                # Продолжаем отправку без изображения
        else:
            logger.debug(f"Заявка #{incident.get('id')} не имеет изображения")
        
        try:
            # MAX API SDK требует chat_id как int или None
            # Используем преобразованный int, если удалось, иначе None (отправка в личный чат)
            chat_id_to_use = self.chat_id_int
            
            if chat_id_to_use is None:
                logger.warning(f"Chat ID не является числом ({self.chat_id_str}), отправка может не сработать")
            
            logger.info(f"Отправка сообщения с attachments={len(attachments) if attachments else 0}")
            
            await bot.send_message(
                chat_id=chat_id_to_use,
                text=message,
                attachments=attachments if attachments else None,
            )
            logger.info(f"Сообщение о заявке #{incident.get('id')} отправлено в чат {chat_id_to_use}")
            return True
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение о заявке #{incident.get('id')}: {e}", exc_info=True)
            logger.debug(f"Chat ID str: {self.chat_id_str}, int: {self.chat_id_int}, Message length: {len(message)}")
            return False
        finally:
            # Очищаем временные файлы
            for attachment in attachments:
                try:
                    if hasattr(attachment, 'path') and attachment.path:
                        if os.path.exists(attachment.path):
                            os.unlink(attachment.path)
                            logger.debug(f"Временный файл удален: {attachment.path}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл: {e}")
    
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
        logger.info(f"Чат для уведомлений: {self.chat_id_str} (int: {self.chat_id_int})")
        
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
