import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

# DB import
from apps.m_DB_manipulation import add_new_word, del_word_for_user, select_for_user, select_len_wordlist


print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = ''  # Ваш токен телеграмм
bot = TeleBot(token_bot, state_storage=state_storage)


known_users = []
userStep = {}
buttons = []

# Глобальные переменные
# Итератор для счёта нашего пакета из 4х слов, по достижению i_iter = 4 делаем запрос на следующий пакет слов
# Для удобства выбрал 4 слова(по заданию 4 кнопки варианта ответа)
i_iter = 0  # Итератор для прохождения по пакету слов из запроса к БД
l_frm_sct = []  # Пакет слов из БД

# Используются при добвалении отношения новых слов
s_en_word = ''
s_ru_word = ''

def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    
    cid = message.chat.id  # id пользователя
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global i_iter  # Необходимость объявления глобальных переменных для сёта вызова функции create_cards()
    global l_frm_sct  # Необходимость объявления глобальных переменных, использование один раз загруженного из запроса к БД пакета слов l_frm_sct при последующих вызовах функции create_cards()
                      # В локальных переменных функция не хранит значения, каждый вызов функции значения обнуляются.
    global buttons
    buttons = []
    
    # Запрос пакета слов из БД при счётчике вызова функции create_cards() равном i_iter = 0, так же передаём i_app_user_id для набора слов доступных данному пользователю
    if i_iter == 0: l_frm_sct = select_for_user(i_app_user_id=cid)  # Запрос из базы данных пакета слов, счётчик i_iter++ при правильном ответе и нажатии кнопки NEXT(произойдёт вызов функции create_cards() = i_iter++)
    
    target_word = f'{l_frm_sct[i_iter][0]}'  # Берём очередное русское слово из пакета по итератору i_iter
    translate = f'{l_frm_sct[i_iter][1]}'  # Берём очередное английское слово из пакета по итератору i_iter
    target_word_btn = types.KeyboardButton(target_word)
    #buttons.append(target_word_btn)  # убрал расширение списка кнопок, иначе выводятся повторно
    
    others = [f'{l_frm_sct[0][0]}', f'{l_frm_sct[1][0]}', f'{l_frm_sct[2][0]}', f'{l_frm_sct[3][0]}']  # Пакет из английских слов(варианты выбора перевода)
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    
    # Итератор для прохода по пакету слов
    i_iter += 1
    if i_iter > 3: i_iter = 0  # отвечаем правильно на пакет из 4х слов и сбрасываем счёт для запроса из БД нового пакета слов
    
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    #buttons.extend([next_btn, add_word_btn, delete_word_btn])  # убрал расширение списка кнопок, иначе выводятся повторно

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


# Фунуция удаления слов из БД
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    
    bot.send_message(cid, text='Введите слово на русском языке для удаления из БД:')
    bot.register_next_step_handler(message, step_del_1)  # Ждём ввода сообщения, при вводе переходим на следующий шаг step_del_1()
    
def step_del_1(message):
    cid = message.chat.id
    ru_word = message.text
    
    # Функция удаления слов "from apps.m_DB_manipulation"
    if del_word_for_user(i_app_user_id = cid, eng_word=None, rus_word=ru_word) == True:
        bot.send_message(message.chat.id, f'Слово "{ru_word}" и его отношения, для пользователя с id = {cid}, удалены из БД')
        
        i_slw = select_len_wordlist(cid)  # Получаем колл.слов изучаемых пользователем
        bot.send_message(message.chat.id, f'колличество изучаемых слов = {i_slw}')
    else:
        bot.send_message(message.chat.id, 'Такого слова нет в БД')
    

# Фунуция добавления новых слов в БД
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    #print(message.text)  # сохранить в БД
    
    bot.send_message(cid, text='Введите слово на русском языке:')
    bot.register_next_step_handler(message, step_add_1)  # Ждём ввода сообщения, при вводе переходим на следующий шаг step_1()
    
def step_add_1(message):
    cid = message.chat.id
    global s_ru_word
    s_ru_word = message.text  # Запись в глобальный регистр для использования в функции add_new_word()
    bot.send_message(message.chat.id, f'Русское слово загружено: "{s_ru_word}"')
    
    bot.send_message(cid, text='Введите слово на английском языке:')
    bot.register_next_step_handler(message, step_add_2)    # Ждём ввода сообщения, при вводе переходим на следующий шаг step_2()
    
def step_add_2(message):
    cid = message.chat.id
    global s_en_word
    s_en_word = message.text  # Запись в глобальный регистр для использования в функции add_new_word()
    bot.send_message(message.chat.id, f'Английское слово загружено: "{s_en_word}"')
    
    # Фунуция добавления новых слов "from apps.m_DB_manipulation"
    add_new_word(eng_word=s_en_word, rus_word=s_ru_word, i_app_user_id=cid)  # вызываем функцию с параметрами пользователя
    bot.send_message(message.chat.id, f'Отношение "{s_ru_word} = {s_en_word}" для пользователя с id = {cid}, добавленно в БД')
    
    i_slw = select_len_wordlist(cid)  # Получаем колл.слов изучаемых пользователем
    bot.send_message(message.chat.id, f'колличество изучаемых слов = {i_slw}')


# Функция ожидающая ввода после выполнения create_cards()
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)