import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8378242193:AAF_ocmxjHPrDvJb_PhaXyFIKwjak96YO5g')
ADMIN_ID = None
REF_LINK = "https://fkwallet.io/registration?partner_code=FKGUFI"
EXAMPLE_SITE = "https://welvar.link/?i=195446"
CHANNEL_LINK = "https://t.me/gufitooooooo"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('/tmp/bot_stats.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
                  last_name TEXT, registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_actions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action_type TEXT, 
                  section TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS link_clicks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, link_url TEXT, 
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('/tmp/bot_stats.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) 
                 VALUES (?, ?, ?, ?)''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def log_action(user_id, action_type, section):
    conn = sqlite3.connect('/tmp/bot_stats.db')
    c = conn.cursor()
    c.execute('''INSERT INTO user_actions (user_id, action_type, section) 
                 VALUES (?, ?, ?)''', (user_id, action_type, section))
    conn.commit()
    conn.close()

def log_link_click(user_id, link_url):
    conn = sqlite3.connect('/tmp/bot_stats.db')
    c = conn.cursor()
    c.execute('''INSERT INTO link_clicks (user_id, link_url) 
                 VALUES (?, ?)''', (user_id, link_url))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('/tmp/bot_stats.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT user_id) FROM user_actions WHERE date(timestamp) = date('now')")
    active_today = c.fetchone()[0]
    
    c.execute('''SELECT section, COUNT(*) FROM user_actions 
                 WHERE action_type = 'section_view' GROUP BY section ORDER BY COUNT(*) DESC''')
    section_stats = c.fetchall()
    
    c.execute('''SELECT link_url, COUNT(*) FROM link_clicks GROUP BY link_url''')
    link_stats = c.fetchall()
    
    conn.close()
    return total_users, active_today, section_stats, link_stats

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    log_action(user.id, 'section_view', 'start')
    
    keyboard = [
        [InlineKeyboardButton("💰 FK Кошелек", callback_data='fk_wallet')],
        [InlineKeyboardButton("🔄 P2P Торговля", callback_data='p2p')],
        [InlineKeyboardButton("🌐 Пополнение сайтов", callback_data='sites')],
        [InlineKeyboardButton("📢 Мой канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🆘 Поддержка", callback_data='support')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=f"🤖 <b>GUFITO FK Helper</b>\n\n"
             f"Привет, {user.first_name}! Я помогу тебе разобраться с FK кошельком, P2P и пополнением сайтов.\n\n"
             f"Выбери раздел:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("💰 FK Кошелек", callback_data='fk_wallet')],
            [InlineKeyboardButton("🔄 P2P Торговля", callback_data='p2p')],
            [InlineKeyboardButton("🌐 Пополнение сайтов", callback_data='sites')],
            [InlineKeyboardButton("📢 Мой канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🆘 Поддержка", callback_data='support')],
            [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🤖 <b>Главное меню</b>\n\nВыбери раздел:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return

    elif query.data == 'fk_wallet':
        log_action(user_id, 'section_view', 'fk_wallet')
        keyboard = [
            [InlineKeyboardButton("📝 Регистрация", callback_data='fk_register')],
            [InlineKeyboardButton("💳 Пополнение", callback_data='fk_deposit')],
            [InlineKeyboardButton("❓ FAQ", callback_data='fk_faq')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="<b>💰 FK Кошелек</b>\n\nВыбери что тебя интересует:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    elif query.data == 'fk_register':
        log_action(user_id, 'section_view', 'fk_register')
        log_link_click(user_id, REF_LINK)
        text = f"<b>📝 РЕГИСТРАЦИЯ В FKWALLET</b>\n\n1. Перейдите по ссылке: {REF_LINK}\n2. Введите email и придумайте надежный пароль\n3. Подтвердите email через письмо на почте\n4. Заполните базовую информацию о себе\n5. Пройдите верификацию для повышения лимитов\n\n<b>✅ Преимущества регистрации по моей ссылке:</b>\n- Быстрая поддержка\n- Бонус при первой операции\n- Доступ к эксклюзивным материалам"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='fk_wallet')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)

    elif query.data == 'fk_deposit':
        log_action(user_id, 'section_view', 'fk_deposit')
        text = "<b>💳 ПОПОЛНЕНИЕ FK WALLET</b>\n\n<b>Способы пополнения:</b>\n• Банковская карта (Visa/Mastercard)\n• P2P-обмен с другими пользователями\n• Криптовалюты (BTC, ETH, USDT)\n• Электронные кошельки\n• Другие платежные системы\n\n<b>Инструкция:</b>\n1. Войдите в личный кабинет\n2. Нажмите 'Пополнить'\n3. Выберите удобный способ\n4. Введите сумму и следуйте инструкциям\n5. Средства зачисляются в течение 15 минут\n\n💡 <i>Минимальная сумма пополнения: 100 рублей</i>"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='fk_wallet')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'fk_faq':
        log_action(user_id, 'section_view', 'fk_faq')
        text = "<b>❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n\n<b>Q: Сколько времени занимает верификация?</b>\nA: Обычно до 24 часов\n\n<b>Q: Какие лимиты у неподтвержденного аккаунта?</b>\nA: До 15 000 руб/сутки, 40 000 руб/месяц\n\n<b>Q: Есть ли комиссия за пополнение?</b>\nA: Зависит от способа, обычно 0-3%\n\n<b>Q: Что делать, если транзакция зависла?</b>\nA: Напишите в поддержку с номером операции\n\n<b>Q: Как восстановить доступ?</b>\nA: Используйте функцию 'Забыли пароль'"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='fk_wallet')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'p2p':
        log_action(user_id, 'section_view', 'p2p')
        keyboard = [
            [InlineKeyboardButton("🛒 Как покупать", callback_data='p2p_buy')],
            [InlineKeyboardButton("💰 Как продавать", callback_data='p2p_sell')],
            [InlineKeyboardButton("🛡️ Безопасность", callback_data='p2p_safety')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "<b>🔄 P2P ТОРГОВЛЯ</b>\n\nP2P (peer-to-peer) — это формат, при котором ты обмениваешься валютой напрямую с другим пользователем.\n\nВ FKwallet такой способ удобен тем, что ты сам выбираешь условия сделки, а платформа помогает сделать её безопасной и прозрачной."
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'p2p_buy':
        log_action(user_id, 'section_view', 'p2p_buy')
        text = "<b>🛒 КАК КУПИТЬ ЧЕРЕЗ P2P</b>\n\n1. В разделе P2P выберите 'Купить'\n2. Укажите валюту и способ оплаты\n3. Выберите продавца по:\n   - Выгодному курсу\n   - Высокому рейтингу\n   - Количеству сделок\n4. Создайте заявку на нужную сумму\n5. Переведите деньги продавцу по указанным реквизитам\n6. Подтвердите оплату в системе\n7. Получите средства на ваш FK кошелек\n\n⏱️ <i>Обычно сделка занимает 5-15 минут</i>"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='p2p')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'p2p_sell':
        log_action(user_id, 'section_view', 'p2p_sell')
        text = "<b>💰 КАК ПРОДАВАТЬ ЧЕРЕЗ P2P</b>\n\n1. В разделе P2P выберите 'Продать'\n2. Создайте объявление с указанием:\n   - Курса продажи\n   - Минимальной/максимальной суммы\n   - Доступных способов оплаты\n3. Ожидайте, когда покупатель создаст сделку\n4. Проверьте поступление денег на вашу карту/кошелек\n5. Подтвердите получение платежа в системе\n6. Средства покупателя автоматически перейдут к вам\n\n📈 <i>Советы для продавцов:</i>\n- Устанавливайте конкурентный курс\n- Быстро подтверждайте сделки\n- Поддерживайте высокий рейтинг"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='p2p')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'p2p_safety':
        log_action(user_id, 'section_view', 'p2p_safety')
        text = "<b>🛡️ МЕРЫ БЕЗОПАСНОСТИ P2P</b>\n\n⚠️ <b>Советы новичкам:</b>\n— Проверяй рейтинг и количество завершённых сделок у другой стороны.\n— Обязательно сверяй реквизиты перед отправкой.\n— Всегда подтверждай только фактически полученные средства.\n\n🔒 <b>Основные правила:</b>\n• Не переводите деньги вне системы P2P\n• Все общение ведите через чат сделки\n• Сохраняйте скриншоты переводов\n• Внимательно читайте условия сделки\n\nP2P — это гибко, выгодно и удобно, особенно если хочется работать с разными валютами и способами оплаты. Главное — подходить к каждой сделке внимательно."
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='p2p')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'sites':
        log_action(user_id, 'section_view', 'sites')
        log_link_click(user_id, EXAMPLE_SITE)
        text = f"<b>🌐 ПОПОЛНЕНИЕ САЙТОВ ЧЕРЕЗ FK</b>\n\n<b>Инструкция:</b>\n1. Авторизуйтесь на нужном сайте\n2. Перейдите в раздел пополнения счета\n3. Выберите 'FK Wallet' как способ оплаты\n4. Введите сумму пополнения\n5. Вас перенаправит в ваш FK кабинет\n6. Подтвердите платеж\n7. Вернитесь на сайт - средства зачислятся автоматически\n\n🎯 <b>Пример сайта:</b> {EXAMPLE_SITE}\n<i>Это проверенный партнер с выгодными условиями!</i>"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)

    elif query.data == 'support':
        log_action(user_id, 'section_view', 'support')
        text = "<b>🆘 ПОДДЕРЖКА</b>\n\nЕсли у вас возникли вопросы или проблемы:\n\n📞 <b>Техническая поддержка FK Wallet:</b>\n• Чат в личном кабинете\n• Email: support@fkwallet.io\n\n👨‍💼 <b>Консультация по боту:</b>\n• Напишите @gufitooooooo\n\nМы поможем решить вашу проблему!"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif query.data == 'stats':
        if ADMIN_ID is None or user_id == ADMIN_ID:
            total_users, active_today, section_stats, link_stats = get_stats()
            
            stats_text = "<b>📊 СТАТИСТИКА БОТА</b>\n\n"
            stats_text += f"👥 <b>Всего пользователей:</b> {total_users}\n"
            stats_text += f"🔥 <b>Активных сегодня:</b> {active_today}\n\n"
            
            stats_text += "<b>📈 Популярные разделы:</b>\n"
            for section, count in section_stats[:5]:
                stats_text += f"• {section}: {count} просмотров\n"
            
            stats_text += "\n<b>🔗 Переходы по ссылкам:</b>\n"
            for link, count in link_stats:
                stats_text += f"• {link}: {count} кликов\n"
            
            if ADMIN_ID is None:
                global ADMIN_ID
                ADMIN_ID = user_id
                stats_text += f"\n⚠️ <i>Ваш ID ({user_id}) установлен как админ</i>"
            
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=stats_text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await query.edit_message_text(text="❌ <b>Доступ запрещен</b>\n\nЭта функция доступна только администратору.", parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id == ADMIN_ID and text.startswith('рассылка:'):
        message_text = text.replace('рассылка:', '').strip()
        
        conn = sqlite3.connect('/tmp/bot_stats.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        conn.close()
        
        success = 0
        failed = 0
        
        for (user_id,) in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 <b>Важное объявление от GUFITO:</b>\n\n{message_text}",
                    parse_mode='HTML'
                )
                success += 1
            except:
                failed += 1
        
        await update.message.reply_text(f"✅ Рассылка завершена!\nУспешно: {success}\nНе удалось: {failed}")

def main():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
