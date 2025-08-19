import telebot
from telebot import types
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'identify',
    'port': 3306
}

bot = telebot.TeleBot('')

def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton('✅ Активувати акаунт'),
        types.KeyboardButton('📜 Правила платформи'),
        types.KeyboardButton('📌 Подати апеляцію')
    )
    bot.send_message(chat_id, 'Оберіть потрібну дію:', reply_markup=markup)
    print(chat_id)

def check_user_in_db(phone_number, chat_id):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            query = "SELECT phone_number, break_rull FROM app_customuser WHERE phone_number = %s;"
            cursor.execute(query, (phone_number,))
            result = cursor.fetchone()
            if result:
                _, break_rull = result
                if break_rull >= 3:
                    return False, True
                update_query = "UPDATE app_customuser SET is_active = %s, telegram_chat_id = %s WHERE phone_number = %s;"
                cursor.execute(update_query, (True, chat_id, phone_number))
                connection.commit()
                return True, False
            else:
                return False, False
    except pymysql.MySQLError as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return False, False
    finally:
        if connection:
            connection.close()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Ласкаво просимо! 👋\n{message.chat.first_name} Вас вітає система Identify')
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda msg: msg.text == '📜 Правила платформи')
def rules(message):
    bot.send_message(message.chat.id, 'Ну, тут будуть якісь правила колись :)')
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda msg: msg.text == '✅ Активувати акаунт')
def activate_account(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_button = types.KeyboardButton(text='Підтвердити реєстрацію', request_contact=True)
    markup.add(phone_button)
    bot.send_message(message.chat.id, 'Надішліть, будь ласка, ваш номер телефону для активації акаунту:', reply_markup=markup)
    bot.register_next_step_handler(message, handle_phone_number)

def handle_phone_number(message):
    if message.contact:
        phone_number = message.contact.phone_number
        chat_id = message.chat.id

        # Очистим номер от пробелов и других нежелательных символов
        phone_number = phone_number.replace(" ", "")  # Убираем пробелы
        
        # Проверим, чтобы номер начинался с "+"
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number  # Если нет, добавляем +


        is_registered, has_break_rulls = check_user_in_db(phone_number, chat_id)
        
        if has_break_rulls:
            bot.send_message(chat_id, 'Ваш акаунт заблоковано через надмірне порушення правил. Зверніться до модерації.')
        elif is_registered:
            bot.send_message(chat_id, 'Дякую, Ваш акаунт активовано!')
        else:
            bot.send_message(chat_id, 'Жоден акаунт не знайдено. Зареєструйтеся на веб-сторінці.')
    else:
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            chat_id = message.chat.id
            bot.send_message(chat_id, 'Скористайтеся кнопкою "Підтвердити реєстрацію".')
        else:
            print("Помилка: не вдалося отримати chat_id")
    show_main_menu(chat_id)

@bot.message_handler(func=lambda msg: msg.text == '📌 Подати апеляцію')
def apeal(message):
    chat_id = message.chat.id
    violated_blogs = get_violated_blogs(chat_id)
    
    if violated_blogs:
        response = 'Виберіть блог, за яким хочете подати апеляцію:\n'
        for i, blog in enumerate(violated_blogs, start=1):
            response += f"{i}. {blog[0]} - Причина: {blog[1]}\n"
        bot.send_message(chat_id, response)
        bot.register_next_step_handler(message, handle_appeal_selection, violated_blogs)
    else:
        bot.send_message(chat_id, 'У вас немає порушень, які вимагають апеляції.')
    
def handle_appeal_selection(message, violated_blogs):
    try:
        selected_index = int(message.text) - 1
        selected_blog = violated_blogs[selected_index]
        bot.send_message(message.chat.id, f"Опишіть апеляцію для блогу '{selected_blog[0]}':")
        bot.register_next_step_handler(message, process_appeal, selected_blog[2])
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "Некоректний вибір. Спробуйте ще раз.")
        apeal(message)

def get_violated_blogs(user_id):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            query = """
            SELECT b.topic, br.reason, br.id
            FROM identify.app_break_rull_blogs br
            JOIN identify.app_blog b ON br.blog_id = b.id
            JOIN identify.app_customuser u ON b.author_id = u.id
            WHERE u.telegram_chat_id = %s AND br.is_appealed = FALSE;
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        if connection:
            connection.close()

def process_appeal(message, blog_id):
    if submit_appeal(blog_id, message.text):
        bot.send_message(message.chat.id, '✅ Ваша апеляція прийнята на розгляд.')
    else:
        bot.send_message(message.chat.id, '❌ Помилка при подачі апеляції.')
    show_main_menu(message.chat.id)

def submit_appeal(blog_id, appeal_text):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            query = "UPDATE app_break_rull_blogs SET appeal = %s, is_appealed = TRUE WHERE id = %s;"
            cursor.execute(query, (appeal_text, blog_id))
            connection.commit()
            return True
    except pymysql.MySQLError as e:
        print(f"Ошибка: {e}")
        return False
    finally:
        if connection:
            connection.close()

def report_user(chat_id, message):
    bot.send_message(
        chat_id, 
        f"Доброго дня, один з Ваших блогів було видалено, причиною тому стало: \"{message}\". "
        "Ви можете продовжувати використання платформи, але, надалі, не порушуйте її правил. "
        "Дякую за розуміння!"
    )
    show_main_menu(chat_id)

    # "При необхідності можете подати апеляцію, вона буде розглянута модераторами в найближчий час. "

def disactive_account(chat_id):
    bot.send_message(
        chat_id,
        f"Ваш акаунт було деактивовано за порушення правил системи Identify. "
        "Для його повторної активації слід вирішити попередні проблеми, через які було видалено блоги."
    )

def verdict_negative(chat_id, blog):
    bot.send_message(
        chat_id,
        f"На превеликий жаль, модерація відхилила Вашу апіляцію, щодо блогу - \"{blog.topic} | {blog.text}\", і його було видалено. "
        "Будь ласка, надалі дотримутеся всіх правил платформи. Дякую за розуміння."    
    )

def verdict_positive(chat_id, blog):
    bot.send_message(
        chat_id,
        f"Вітаємо, Ваша апеляція щодо блогу - \"{blog.topic} | {blog.text}\", була успішною. "
        "Тепер блог став публічним, але, надалі, не забувайте дотримуватися правил платформи!"
    )

if __name__ == '__main__':
    bot.infinity_polling()
