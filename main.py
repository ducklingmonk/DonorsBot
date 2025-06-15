import os
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from data import MENU_TREE, ANSWERS

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
RENDER_URL = os.getenv("RENDER_URL")

# Styled "Back" button
BACK_BUTTON = "⬅️ Назад"
CUSTOM_QUESTION_BUTTON = "Свой вопрос❓"
# Track user navigation state {user_id: ["Main Menu", "Kell+", ...]}
user_navigation = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show main menu"""
    user_id = update.effective_user.id
    user_navigation[user_id] = ["Main Menu"]  # Reset navigation state

    keyboard = [
                   [category] for category in MENU_TREE.keys()
               ] + [[CUSTOM_QUESTION_BUTTON]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🩸 Вас приветствует бот для доноров крови\n"
        "Выберите интересующую вас категорию:",
        reply_markup=reply_markup
    )

async def show_current_menu(update: Update, path):
    node = get_node_from_path(path)

    if node is None:
        path = ["Main Menu"]
        node = MENU_TREE

    keyboard = []
    if isinstance(node, dict):
        keyboard = [[item] for item in node.keys()]

    # Добавляем кнопку "Назад" (если не в главном меню)
    if len(path) > 1:
        keyboard.append([BACK_BUTTON])
    # Добавляем "Свой вопрос" ТОЛЬКО в главном меню
    elif len(path) == 1:
        keyboard.append([CUSTOM_QUESTION_BUTTON])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if path[-1] == "Main Menu":
        message = "Выберите категорию:"
    else:
        message = f"Выберите подкатегорию ({' > '.join(path[1:])}):"

    await update.message.reply_text(message, reply_markup=reply_markup)


def get_node_from_path(path):
    """Safe path navigation that preserves your restart logic"""
    if not path or path[-1] == "Main Menu":
        return MENU_TREE

    node = MENU_TREE
    for step in path[1:]:  # Skip "Main Menu"
        if isinstance(node, dict) and step in node:
            node = node[step]
        else:
            return None
    return node


def get_answer_from_path(full_path: list) -> str:
    """Exact path matching for duplicate menu items"""
    node = MENU_TREE
    for step in full_path[1:]:  # Skip "Main Menu"
        if isinstance(node, dict) and step in node:
            node = node[step]
        else:
            return None
    return ANSWERS.get(node) if isinstance(node, str) else None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # YOUR RESTART LOGIC (preserved exactly)
    if user_id not in user_navigation:
        await start(update, context)  # Your original restart call
        return

    current_path = user_navigation[user_id]

    # Handle special buttons
    if user_message == BACK_BUTTON:
        if len(current_path) > 1:
            current_path.pop()
        return await show_current_menu(update, current_path)

    if user_message == CUSTOM_QUESTION_BUTTON:
        await update.message.reply_text("Напишите свой вопрос в строке ниже, и мы ответим вам в ближайшее время.")
        return

    # 1. Try exact path-based answer first
    test_path = current_path + [user_message]
    answer = get_answer_from_path(test_path)
    if answer:
        if isinstance(answer, dict):
            if "photo_url" in answer:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=answer["photo_url"],
                    caption=answer.get("text", "")
                )
            else:
                await update.message.reply_text(answer.get("text", ""), parse_mode='HTML')
        else:
            await update.message.reply_text(answer, parse_mode='HTML')
        return await show_current_menu(update, current_path)

    # 2. Handle menu navigation
    current_node = get_node_from_path(current_path)
    if isinstance(current_node, dict) and user_message in current_node:
        next_node = current_node[user_message]

        # Если ключ в автоответных и есть ответ
        if user_message in AUTO_REPLY_KEYS:
            full_path = current_path + [user_message]
            answer = get_answer_from_path(full_path)
            if answer:
                await update.message.reply_text(answer, parse_mode='HTML')

        if isinstance(next_node, dict):  # Переход в подменю
            current_path.append(user_message)

        elif isinstance(next_node, str):  # Конечный ответ
            answer = ANSWERS.get(next_node, "Извините, ответ не найден.")
            await update.message.reply_text(answer)

        return await show_current_menu(update, current_path)

    # 3. Handle main category switches
    if user_message in MENU_TREE:
        user_navigation[user_id] = ["Main Menu", user_message]
        return await show_current_menu(update, user_navigation[user_id])

    # YOUR ORIGINAL FORWARDING LOGIC (preserved exactly)
    if len(current_path) > 1:
        return await show_current_menu(update, current_path)
    else:
        await forward_to_manager(update, context)  # Your original forwarding

async def forward_to_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward user's question to manager group"""
    if not MANAGER_GROUP_CHAT_ID:
        await update.message.reply_text("Извините, сервис временно недоступен.")
        return

    try:
        user = update.effective_user
        message = (
            f"Вопрос от @{user.username}:\n"
            f"{update.message.text}\n"
        )

        await context.bot.send_message(
            chat_id=MANAGER_GROUP_CHAT_ID,
            text=message
        )
        await update.message.reply_text(
            "✅ Ваш вопрос передан менеджеру. Мы ответим вам в ближайшее время.\n"
            "Вы можете продолжать пользоваться меню ниже:"
        )
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке вопроса. Пожалуйста, попробуйте позже."
        )


async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден!")

    app = Application.builder().token(TOKEN).build()

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
            webhook_url=f"{RENDER_URL}{TOKEN}"
        )

        # Бесконечное ожидание через asyncio
        await asyncio.get_event_loop().create_future()
    except asyncio.CancelledError:
        logger.info("Получен сигнал завершения")
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
