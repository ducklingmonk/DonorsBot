import os
import logging
import asyncpg
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import urlparse
import asyncio
from data import QUESTIONS, REPLIES

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

    logger.info(
        f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) отправил сообщение: {user_message}"
    )
    # Пропускаем ВСЕ сообщения из группы менеджеров
    if update.message.chat.id == MANAGER_GROUP_CHAT_ID:
        logger.info(f"Сообщение из группы менеджеров пропущено")
        return

    if user_message == "Свой вопрос❓":
        # Handle "Задать вопрос менеджеру" button
        await update.message.reply_text("Напишите вопрос в строке ниже и в ближайшее время организатор ответит Вам")
        logger.info(
            f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) нажал кнопку 'Свой вопрос❓'.")
    elif user_message in REPLIES:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=REPLIES[user_message],
            parse_mode="HTML"
        )
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
                        # Отправляем ОЧИЩЕННОЕ сообщение вместо оригинального
                        forwarded = await context.bot.send_message(
                            chat_id=MANAGER_GROUP_CHAT_ID,
                            text=f"От @{user_username}:\n{user_message}"
                        )
                        # Only insert into DB if forwarding was successful.
                        await db.execute(
                            "INSERT INTO messages (user_chat_id, user_message_id, group_message_id) VALUES ($1, $2, $3)",
                            user_chat_id, user_message_id, forwarded.message_id
                        )

                        logger.info(
                            f"[handle_message] Сообщение пользователя @{user_username} (ID: {user_chat_id}) переслано в группу менеджеров (ID: {MANAGER_GROUP_CHAT_ID}). ID пересланного сообщения: {forwarded.message_id}."
                        )
                        await update.message.reply_text("✅ Ваш вопрос передан. Ожидайте ответа.")

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

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден!")

    db = await init_db()
    app = Application.builder().token(TOKEN).build()
    app.bot_data['db'] = db

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
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

