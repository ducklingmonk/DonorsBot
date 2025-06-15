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

    # Фильтруем только ключи, не начинающиеся с "_"
    if isinstance(node, dict):
        visible_keys = [k for k in node.keys() if not k.startswith("_")]
        keyboard = [[item] for item in visible_keys]
    else:
        keyboard = []

    # Назад / Свой вопрос
    if len(path) > 1:
        keyboard.append([BACK_BUTTON])
    elif len(path) == 1:
        keyboard.append([CUSTOM_QUESTION_BUTTON])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Просто обновляем клавиатуру, не отправляя текст
    await update.message.reply_text(
        text="\u200b",  # <- no caption
        reply_markup=reply_markup
    )

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

async def send_answer(update, context, answer):
    if answer is None:
        await update.message.reply_text("Извините, ответ не найден."); return

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text

    # ── Перезапуск, «Назад», «Свой вопрос»
    if user_id not in user_navigation:
        await start(update, context); return
    path = user_navigation[user_id]

    if msg == BACK_BUTTON:
        if len(path) > 1: path.pop()
        return await show_current_menu(update, path)

    if msg == CUSTOM_QUESTION_BUTTON:
        await update.message.reply_text("Напишите свой вопрос в строке ниже, и мы ответим вам в ближайшее время.")
        return

    # ── Достали текущий узел и проверили, есть ли такой пункт
    node = get_node_from_path(path)
    if isinstance(node, dict) and msg in node:
        next_node = node[msg]

        # ①  Если next_node — dict c _answer  →  присылаем, а затем входим в подменю
        if isinstance(next_node, dict) and "_answer" in next_node:
            answer_key = next_node["_answer"]
            await send_answer(update, context, ANSWERS.get(answer_key))
            path.append(msg)                    # перейти внутрь
            return await show_current_menu(update, path)

        # ②  Если next_node — конечная строка‑ключ
        if isinstance(next_node, str):
            await send_answer(update, context, ANSWERS.get(next_node))
            return await show_current_menu(update, path)

        # ③  Обычное подменю‑словарь без _answer
        if isinstance(next_node, dict):
            path.append(msg)
            return await show_current_menu(update, path)

    # ── Переход из главного меню
    if msg in MENU_TREE:
        user_navigation[user_id] = ["Main Menu", msg]
        return await show_current_menu(update, user_navigation[user_id])

    # ── Не распознали — шлём менеджеру
    if len(path) > 1:
        return await show_current_menu(update, path)
    await forward_to_manager(update, context)


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
