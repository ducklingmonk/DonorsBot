import os
import logging
import asyncpg
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import urlparse
import asyncio
from data import QUESTIONS, REPLIES
# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)
logger = logging.getLogger(__name__)

# Load manager group chat ID from environment variable
MANAGER_GROUP_CHAT_ID = int(os.getenv("MANAGER_GROUP_CHAT_ID", 0))  # Replace with your manager group ID
TEMBO_DB_URL = os.getenv("TEMBO_DATABASE_URL")
RENDER_URL = os.getenv("RENDER_URL")

# Инициализация базы данных
async def init_db():
    try:
        parsed = urlparse(TEMBO_DB_URL)
        conn = await asyncpg.connect(
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            host=parsed.hostname,
            port=parsed.port,
            ssl="require"
        )
        logger.info("Successfully connected to Tembo PostgreSQL")
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        raise

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_chat_id BIGINT NOT NULL,
            user_message_id INT NOT NULL,
            group_message_id INT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id SERIAL PRIMARY KEY,
            message_id INT REFERENCES messages(id) ON DELETE CASCADE,
            group_reply_id INT NOT NULL,
            chat_reply_id INT NOT NULL,
            content TEXT NOT NULL,
            is_deleted BOOLEAN DEFAULT FALSE,
            edited_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    logger.info("Проверка таблицы messages: OK")

    return conn

async def reconnect_db():
    db_conn = None
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            parsed = urlparse(TEMBO_DB_URL)
            db_conn = await asyncpg.connect(
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                host=parsed.hostname,
                port=parsed.port,
                ssl="require"
            )
            logger.info(f"Successfully reconnected to Tembo PostgreSQL (attempt {attempt}/{retries}).")
            return db_conn
        except Exception as e:
            logger.error(f"Database connection failed (attempt {attempt}/{retries}): {e}")
            await asyncio.sleep(2**attempt) # Exponential backoff
    logger.error("Failed to reconnect to the database after multiple attempts.")
    return None

# Styled "Back" button
BACK_BUTTON = "⬅️ Назад"

# Dictionary to store the relationship between user and forwarded messages
user_manager_messages = {}


# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} started the bot.")
    # Create keyboard layout
    keyboard = [
                   [question] for question in QUESTIONS  # Each question is in its own row
               ] + [
                   ["Свой вопрос❓"]  # Additional button in its own row
               ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вас приветствует бот для доноров🩸\n"
        "Вы можете написать вопрос менеджеру в строке ниже или выбрать категорию часто задаваемых вопросов:",
        reply_markup=reply_markup
    )


# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_chat_id = update.message.chat_id
    user_message_id = update.message.message_id
    user_username = update.message.from_user.username

    # Log the received message
    logger.info(
        f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) отправил сообщение: {user_message}")
    # Пропускаем ВСЕ сообщения из группы менеджеров
    if update.message.chat.id == MANAGER_GROUP_CHAT_ID:
        logger.info(f"Сообщение из группы менеджеров пропущено")
        return

    if user_message == "Свой вопрос❓":
        await update.message.reply_text("Напишите вопрос в строке ниже и в ближайшее время организатор ответит Вам")
        logger.info(
            f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) нажал кнопку 'Свой вопрос❓")
    elif user_message in REPLIES:
        # Send the answer if the question is in the list
        await update.message.reply_text(REPLIES[user_message])
        logger.info(
            f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) задал вопрос: {user_message}. Ответ: {REPLIES[user_message]}")
    else:
        try:
            db = context.bot_data['db']
            if db is None or db.is_closed():
                db = await reconnect_db()
                context.bot_data['db'] = db
                logger.info("Reconnection?")
                if db is None:
                    raise Exception("Failed to connect to database")
            logger.info("Connection success!")
            if MANAGER_GROUP_CHAT_ID:
                try:
                    async with db.transaction():  # Wrap everything in a transaction
                        # Forward the message and store the result in the database.
                        forwarded = await context.bot.forward_message(
                            MANAGER_GROUP_CHAT_ID,
                            user_chat_id,
                            user_message_id
                        )

                        # Only insert into DB if forwarding was successful.
                        await db.execute(
                            "INSERT INTO messages (user_chat_id, user_message_id, group_message_id) VALUES ($1, $2, $3)",
                            user_chat_id, user_message_id, forwarded.message_id
                        )

                        logger.info(
                            f"[handle_message] Сообщение пользователя @{user_username} (ID: {user_chat_id}) переслано в группу менеджеров (ID: {MANAGER_GROUP_CHAT_ID}). ID пересланного сообщения: {forwarded.message_id}."
                        )
                        await update.message.reply_text("✅ Ваш вопрос передан менеджеру. Ожидайте ответа.")

                except Exception as e:
                    logger.error(f"Ошибка пересылки или записи в базу данных: {e}")
                    await update.message.reply_text(
                        "❌ Произошла ошибка при пересылке вопроса менеджеру. Пожалуйста, попробуйте позже."
                    )

            else:
                logger.warning("[handle_message] ID группы менеджеров не настроен.")
                await update.message.reply_text(
                    "В настоящее время нет доступных менеджеров. Пожалуйста, попробуйте позже.")

        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            await update.message.reply_text("❌ Произошла неизвестная ошибка. Пожалуйста, попробуйте позже.")

async def handle_manager_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Entering handle_manager_reply")
    try:
        if not update.message or not update.message.reply_to_message:
            logger.debug("Пустое сообщение или отсутствие ответа")
            return

        message = update.message
        replied_msg = message.reply_to_message

        logger.debug(f"Processing reply to message {replied_msg.message_id} in chat {message.chat.id}")

        # Проверка что это ответ на сообщение бота
        if replied_msg.from_user.id != context.bot.id:
            logger.debug("Ответ не на сообщение бота")
            return

        group_message_id = replied_msg.message_id
        logger.debug(f"Looking up group_message_id {group_message_id} in DB")

        db = context.bot_data['db']
        if db is None or db.is_closed():
            db = await reconnect_db()
            context.bot_data['db'] = db
            logger.info("Reconnection?")
            if db is None:
                raise Exception("Failed to connect to database")

        logger.info("Connection success!")

        # Ищем оригинальное сообщение в БД
        record = await context.bot_data['db'].fetchrow(
            "SELECT user_chat_id, user_message_id FROM messages WHERE group_message_id = $1",
            group_message_id
        )

        if not record:
            logger.warning(f"Сообщение {group_message_id} не найдено в БД")
            return

        # Отправляем ответ пользователю
        sent = await context.bot.send_message(
            record['user_chat_id'],
            f"📩 Ответ менеджера:\n{message.text}",
            reply_to_message_id=record['user_message_id']
        )
        logger.info(f"Ответ отправлен пользователю {record['user_chat_id']}")

        # Сохраняем связь ответов
        await context.bot_data['db'].execute(
            """INSERT INTO replies(message_id, group_reply_id, chat_reply_id, content)
            VALUES((SELECT id FROM messages WHERE group_message_id = $1), $2, $3, $4)""",
            group_message_id, message.message_id, sent.message_id, message.text
        )
        logger.debug(f"Inserted reply into DB: group_reply_id={message.message_id}")

    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {str(e)}", exc_info=True)

# Проверка прав администратора
async def check_admin_rights(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        member = await context.bot.get_chat_member(
            chat_id=chat_id,
            user_id=context.bot.id
        )
        return member.can_delete_messages
    except Exception as e:
        logger.error(f"Ошибка проверки прав: {e}")
        return False


async def delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Проверка прав администратора
        if not await check_admin_rights(context, MANAGER_GROUP_CHAT_ID):
            await update.message.reply_text("⚠️ Требуются права администратора!")
            return

        # Проверка сообщения
        if not update.message or not update.message.reply_to_message:
            logger.warning("Пустой запрос на удаление")
            return

        replied_msg = update.message.reply_to_message
        replied_msg_id = replied_msg.message_id

        # Поиск записи в БД
        async with context.bot_data['db'].transaction():
            record = await context.bot_data['db'].fetchrow(
                """SELECT m.user_chat_id, r.chat_reply_id 
                FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE r.group_reply_id = $1""",
                replied_msg_id
            )

            if not record:
                logger.warning(f"Сообщение {replied_msg_id} не найдено")
                await update.message.reply_text("❌ Сообщение не найдено")
                return

            # Удаление у пользователя
            await context.bot.delete_message(
                chat_id=record['user_chat_id'],
                message_id=record['chat_reply_id']
            )

            # Обновление статуса
            await context.bot_data['db'].execute(
                "UPDATE replies SET is_deleted = TRUE WHERE group_reply_id = $1",
                replied_msg_id
            )

        await update.message.reply_text("✅ Ответ удален у пользователя")
        logger.info(f"Сообщение {replied_msg_id} удалено")

    except Exception as e:
        logger.error(f"Ошибка удаления: {str(e)}")
        await update.message.reply_text("❌ Ошибка удаления")


async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        edited = update.edited_message
        if not edited or edited.chat.id != MANAGER_GROUP_CHAT_ID:
            logger.debug("Ignoring edit from non-manager group")
            return
        # Безопасное получение edited_message
        edited = getattr(update, 'edited_message', None)
        if not edited:
            logger.debug("Не является редактированным сообщением")
            return

        # Безопасное получение информации о пользователе
        user = getattr(edited, 'from_user', None)
        if not user:
            logger.warning("Не удалось получить информацию об отправителе")
            return

        logger.info(f"Попытка редактирования от @{user.username}")

        # Проверка чата
        if edited.chat.id != MANAGER_GROUP_CHAT_ID:
            logger.debug(f"Сообщение из чата {edited.chat.id}, пропускаем")
            return

        # Поиск связанного сообщения
        async with context.bot_data['db'].transaction():
            reply = await context.bot_data['db'].fetchrow(
                """SELECT r.chat_reply_id, m.user_chat_id 
                FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE r.group_reply_id = $1""",
                edited.message_id
            )

            if not reply:
                logger.warning(f"Сообщение {edited.message_id} не найдено в БД")
                return

            if reply.get('is_deleted'):
                logger.info(f"Сообщение {edited.message_id} уже удалено")
                return

            # Обновление текста
            await context.bot.edit_message_text(
                chat_id=reply['user_chat_id'],
                message_id=reply['chat_reply_id'],
                text=f"✏️ Ответ менеджера:\n{edited.text}"
            )

            # Обновление записи в БД
            await context.bot_data['db'].execute(
                """UPDATE replies 
                SET content = $1, edited_at = NOW() 
                WHERE group_reply_id = $2""",
                edited.text, edited.message_id
            )

        logger.info(f"Сообщение {edited.message_id} успешно обновлено")

    except Exception as e:
        logger.error(f"Ошибка редактирования: {str(e)}")
        if edited:
            logger.debug(f"Данные сообщения: {edited.to_dict()}")


async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден!")

    db = await init_db()
    app = Application.builder().token(TOKEN).build()
    app.bot_data['db'] = db

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("delete", delete_reply))
    app.add_handler(MessageHandler(
        filters.Chat(MANAGER_GROUP_CHAT_ID) &
        filters.REPLY &
        filters.UpdateType.EDITED_MESSAGE,  # 👈 Only edited replies
        handle_edit
    ))
    app.add_handler(MessageHandler(
        filters.Chat(MANAGER_GROUP_CHAT_ID) &
        filters.REPLY &
        filters.UpdateType.MESSAGE,  # 👈 Only new replies
        handle_manager_reply
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск вебхука
    await app.initialize()
    await app.start()

    try:
        PORT = int(os.environ.get("PORT", 10000))
        await app.updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_URL}{TOKEN}",
            drop_pending_updates=True
        )

        # Бесконечное ожидание через asyncio
        await asyncio.get_event_loop().create_future()

    except asyncio.CancelledError:
        logger.info("Получен сигнал завершения")
    finally:
        await app.stop()
        await app.shutdown()
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

