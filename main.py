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
    """Show menu for current navigation path"""
    node = get_node_from_path(path)

    if node is None:
        path = ["Main Menu"]
        node = MENU_TREE

    keyboard = []
    if isinstance(node, dict):
        keyboard = [[item] for item in node.keys()]

    # Add Back button if not in main menu
    if len(path) > 1:
        keyboard.append([BACK_BUTTON])
    # Add custom question only in main menu
    elif len(path) == 1:
        keyboard.append([CUSTOM_QUESTION_BUTTON])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if path[-1] == "Main Menu":
        message = "Выберите категорию:"
    else:
        message = f"Выберите подкатегорию ({' > '.join(path[1:])}):"

    await update.message.reply_text(message, reply_markup=reply_markup)


def get_node_from_path(path):
    """Get current node in menu tree based on navigation path"""
    if path[-1] == "Main Menu":
        return MENU_TREE

    node = MENU_TREE
    for step in path[1:]:  # Skip "Main Menu"
        if step in node:
            node = node[step]
            # Removed the string check to allow proper navigation
        else:
            return None
    return node


def find_matching_answer(question):
    """Searches all menu items for matching text (case-insensitive)"""
    question = question.lower()
    # Check both menu items and direct answer keys
    for key, value in MENU_TREE.items():
        if question == key.lower():
            if isinstance(value, str):
                return ANSWERS.get(value)

    stack = list(MENU_TREE.values())
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for item, value in node.items():
                if question == item.lower():
                    if isinstance(value, str):
                        return ANSWERS.get(value)
                elif isinstance(value, dict):
                    stack.append(value)
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Initialize navigation if needed
    if user_id not in user_navigation:
        user_navigation[user_id] = ["Main Menu"]

    current_path = user_navigation[user_id]
    logger.debug(f"User {user_id} at path {current_path} selected: {user_message}")

    # Handle back button
    if user_message == BACK_BUTTON:
        if len(current_path) > 1:
            current_path.pop()  # Go back one level
        return await show_current_menu(update, current_path)

    # Handle custom question
    if user_message == CUSTOM_QUESTION_BUTTON:
        await update.message.reply_text("Напишите свой вопрос в строке ниже:")
        return

    # FIRST check if this is a direct answer
    answer = find_matching_answer(user_message)
    if answer:
        await update.message.reply_text(answer)
        return await show_current_menu(update, current_path)

    # THEN handle menu navigation
    current_node = get_node_from_path(current_path)

    if current_node is None:
        return await show_current_menu(update, ["Main Menu"])

    if isinstance(current_node, dict) and user_message in current_node:
        next_node = current_node[user_message]

        if isinstance(next_node, dict):  # Submenu
            current_path.append(user_message)
            return await show_current_menu(update, current_path)
        else:  # Answer reference
            answer = ANSWERS.get(next_node, "Извините, ответ не найден.")
            await update.message.reply_text(answer)
            # Stay at current level after showing answer
            return await show_current_menu(update, current_path)

    # If selection is another main category while in submenu
    if user_message in MENU_TREE:
        user_navigation[user_id] = ["Main Menu", user_message]
        return await show_current_menu(update, user_navigation[user_id])

    # Unrecognized input - show current menu
    await show_current_menu(update, current_path)


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