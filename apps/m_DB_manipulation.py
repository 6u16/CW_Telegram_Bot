# Курсовая работа «ТГ-чат-бот «Обучалка английскому языку»» по курсу «Базы данных»

import json
import os
import sqlalchemy
import sqlalchemy as sq
import random

from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import and_
from pprint import pprint

Base = declarative_base()


# CREATE TABLE
class Eng_words(Base):
    __tablename__ = "Eng_words"

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    word = sq.Column(sq.String(length=40), nullable=False)

    def __str__(self):  # для удобства извлчения данных
        return f'Eng_words: {self.id}: {self.word}'
    

class Rus_words(Base):
    __tablename__ = "Rus_words"

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    word = sq.Column(sq.String(length=40), nullable=False)

    def __str__(self):  # для удобства извлчения данных
        return f'Rus_words: {self.id}: {self.word}'
    

class Stock(Base):
    __tablename__ = "Stock"

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    id_eng_wd = sq.Column(sq.Integer, sq.ForeignKey("Eng_words.id", ondelete='CASCADE'), nullable=False)  # ondelete='CASCADE' -  - для удаления каскадом
    id_rus_wd = sq.Column(sq.Integer, sq.ForeignKey("Rus_words.id", ondelete='CASCADE'), nullable=False)
    
    eng_wd = relationship(Eng_words, backref="Eng_wds", passive_deletes=True)  # passive_deletes=True - для удаления каскадом
    rus_wd = relationship(Rus_words, backref="Rus_wds", passive_deletes=True)

    def __str__(self):  # для удобства извлчения данных
        return f'Stock: {self.id}: ({self.id_eng_wd}, {self.id_rus_wd})'
    
    
class Collection(Base):
    __tablename__ = "Collection"

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    id_user = sq.Column(sq.Integer)
    id_words = sq.Column(sq.Integer, sq.ForeignKey("Stock.id", ondelete='CASCADE'), nullable=False)

    stock = relationship(Stock, backref="Coll_user", passive_deletes=True)  # passive_deletes=True - для удаления каскадом
    
    def __str__(self):  # для удобства извлчения данных
        return f'Stock: {self.id}: ({self.id_user}, {self.id_words})'


# Создание таблиц
def create_tables(engine) -> None:
    Base.metadata.drop_all(engine)  # Удаление всех таблиц из БД
    Base.metadata.create_all(engine)  # Создание наших таблиц
    print('База создана')


# Параметры подключения    
s_BD = 'postgresql'
s_BD_lgn = 'postgres'
s_BD_psswrd = 'postgres'
s_BD_lclhst = '5432'
s_BD_name = 'CW_DB_Telegram'

DSN = f'{s_BD}://{s_BD_lgn}:{s_BD_psswrd}@localhost:{s_BD_lclhst}/{s_BD_name}'
engine = sqlalchemy.create_engine(DSN) # create_engine() - Движок для подключения к базе данных, принимает на вход DSN URL
create_tables(engine) # Вызываем функцию создания таблиц

Session = sessionmaker(bind=engine) # sessionmaker - объект принимает на вход движок и создаёт сессию
session = Session()


# Заполнение таблицы из файла json с помощью создания моделей
file_path = os.path.join(os.getcwd(), '/data/English_dict.json')  # Строительство пути
with open(file_path, 'r', encoding='utf-8') as fd:
    data = json.load(fd)

for element in data:
    if element.get('model') == 'eng_words':
        obj = Eng_words\
                (id=element.get('pk'),\
                word=element.get('fields', {}).get('word', {}))
        session.add(obj)
    if element.get('model') == 'rus_words':
        obj = Rus_words\
                (id=element.get('pk'),\
                word=element.get('fields', {}).get('word', {}))
        session.add(obj)
    if element.get('model') == 'stock':      
        obj = Stock\
                (id=element.get('pk'),\
                id_eng_wd=element.get('fields', {}).get('id_eng_wd', {}),\
                id_rus_wd=element.get('fields', {}).get('id_rus_wd', {}))
        session.add(obj)
    if element.get('model') == 'collection':      
        obj = Collection\
                (id=element.get('pk'),\
                id_user=element.get('fields', {}).get('id_user', {}),\
                id_words=element.get('fields', {}).get('id_words', {}))
        session.add(obj)

session.commit()


# Функция добавления слов для конкретного пользователя
def add_new_word(eng_word, rus_word, i_app_user_id) -> None:
    
    # создаем сессию подключения к бд
    with Session(autoflush=True, bind=engine) as db:
        
        max_id = session.query(func.max(Stock.id)).scalar()  # узнаём крайний id

        word_1 = Eng_words(word=f'{eng_word}', id=max_id+1)  # добавляем слово и id++ в экземпляр класса
        word_2 = Rus_words(word=f'{rus_word}', id=max_id+1)
        stock_add = Stock(id=max_id+1, id_eng_wd=max_id+1, id_rus_wd=max_id+1)  # добавляем отношение слов++, и id++
        collect_add = Collection(id=max_id+1, id_user=i_app_user_id, id_words=max_id+1)  # добавляем в коллекцию конкретного(i_app_user_id) пользователя
        
        db.add_all([word_1, word_2, stock_add, collect_add])  # добавляем в бд
        db.commit()     # сохраняем изменения
        print('слово в базе')
    

# Функция удаления слов(администратор)
def del_word(eng_word=None, rus_word=None) -> None:
    
    if rus_word:
        id = session.query(Stock).join(Rus_words).filter(Rus_words.word == rus_word)
        for b in id.all():
            print(b.id_eng_wd)
        session.query(Eng_words).filter(Eng_words.id == b.id_eng_wd).delete()
        session.query(Rus_words).filter(Rus_words.word == rus_word).delete()
        
    if eng_word:
        id = session.query(Stock).join(Eng_words).filter(Eng_words.word == eng_word)
        for b1 in id.all():
            print(b1.id_rus_wd)
        session.query(Rus_words).filter(Rus_words.id == b1.id_rus_wd).delete()
        session.query(Eng_words).filter(Eng_words.word == eng_word).delete()
        
    session.commit()  # фиксируем изменения
    print('слово удалено')
    

# Функция удаления слов для конкретного пользователя
def del_word_for_user(i_app_user_id, eng_word=None, rus_word=None) -> bool:
    
    # Получаем информацию о наличии удаляемого слова
    l_id_user = []  # список id слов доступных пользователю
    query = session.query(Rus_words).join(Stock.rus_wd).join(Collection).filter(Collection.id_user ==i_app_user_id)  # запрос списка доступных слов конкретному пользователю, список id слов
    
    for b in query.all():  
        l_id_user.append(b.word)
        
    print(l_id_user)
    
    if not l_id_user.count(rus_word):  # Если слова нет
        print('Такого слова нет в БД')
        return False
    
    if rus_word:
        qwery = session.query(Collection).join(Stock).join(Rus_words).filter(Rus_words.word == rus_word)  # Собираем данные по слову выбранному для удаления
        for b in qwery.all():  # Слова могут быть одинаковые но у разных пользователей
            print(b.stock.id_eng_wd)
            print(b.id_user)
            print(b.id_words)
            if b.id_user == i_app_user_id:  # Удаляем слово у конкретного пользователя 
                session.query(Collection).filter(and_(Collection.id_user == i_app_user_id, Collection.id_words == b.id_words)).delete()  # Удаляем из коллекции совпадение по слову и id пользователя
                session.query(Eng_words).filter(Eng_words.id == b.stock.id_eng_wd).delete()  # Удаляем слова из таблиц *_words
                session.query(Rus_words).filter(Rus_words.id == b.stock.id_eng_wd).delete()
                
    if eng_word:
        qwery = session.query(Collection).join(Stock).join(Eng_words).filter(Eng_words.word == eng_word)
        for b in qwery.all():
            print(b.stock.id_rus_wd)
            print(b.id_user)
            print(b.id_words)
            if b.id_user == i_app_user_id:
                session.query(Collection).filter(and_(Collection.id_user == i_app_user_id, Collection.id_words == b.id_words)).delete()
                session.query(Eng_words).filter(Eng_words.id == b.stock.id_rus_wd).delete()
                session.query(Rus_words).filter(Rus_words.id == b.stock.id_rus_wd).delete()
        
    session.commit()  # фиксируем изменения
    print('слово удалено')
    return True


# Делаем запрос пакета слов, из диапазона 0 - max_id (все слова доступны всем)
def select_all() -> list:
    
    b_immort = False
    l_rand = []
    max_id = session.query(func.max(Eng_words.id)).scalar()  # узнаём крайний id
    
    while b_immort == False:
            
        i_rand = random.randrange(1, max_id+1)  # Выбираем числа из диапазона id+1 DB
        if not l_rand.count(i_rand):  # Записываем в список для избежания повторения
            l_rand.append(i_rand)
            
        if len(l_rand)==4:  # Определяем размер списка(пакета слов) 
            print(l_rand)
            subq_03 = session.query(Stock).join(Eng_words).join(Rus_words).filter(Rus_words.id.in_(l_rand))  # .id.in_(l_rand) - Запрос списком id 
            l_rand = []
            for b in subq_03.all():  # Записываем в удобный нам формат данных
                l_rand.append([b.eng_wd.word,b.rus_wd.word])
            b_immort = True
                
    session.commit()
    
    return l_rand


# Делаем запрос пакета слов, из диапазона 0 - max_id конкретного ПОЛЬЗОВАТЕЛЯ!!!!(i_app_user_id)
def select_for_user(i_app_user_id) -> list:
    
    b_immort = False
    l_user_info = [0, i_app_user_id]  # Параметры пользователя, доступный список id слов конкретному пользователю [0, - общий для всех список
    l_rand = []  # список(пакет) случайно выбранных id / список слов из запроса
    l_id_user = []  # список id слов доступных пользователю
    
    query = session.query(Collection).filter(Collection.id_user.in_(l_user_info))  # запрос списка доступных слов конкретному пользователю, список id слов
    
    for b in query.all():  
        l_id_user.append(b.id_words)
    
    print(l_id_user)
    
    while b_immort == False:   
        
        i_rand = random.choice(l_id_user)  # Выбираем числа из диапазона id доступных слов конкретному пользователю
        
        if not l_rand.count(i_rand):  # Создаём список для избежания повторения
            l_rand.append(i_rand)
        
        # когда список l_rand достигает нужного объёма пакета(4), отправляем запрос этим списком на получение пакета слов
        if len(l_rand)==4:  # Определяем размер списка(пакета слов) 
            print(l_rand)
            subq_03 = session.query(Stock).join(Eng_words).join(Rus_words).filter(Rus_words.id.in_(l_rand))  # .id.in_(l_rand) - Запрос списком id 
            l_rand = []
            
            for b in subq_03.all():  # Записываем в удобный нам формат данных
                l_rand.append([b.eng_wd.word,b.rus_wd.word])
            b_immort = True
    
    print(l_rand)
    session.commit()
    
    return l_rand


# Функция запроса колл.слов изучаемых пользователем
def select_len_wordlist(i_app_user_id) -> int:
    
    l_user_info = [0, i_app_user_id]  # Параметры пользователя, доступный список id слов конкретному пользователю [0, - общий для всех список
    l_id_user = []  # список id слов доступных пользователю
    
    query = session.query(Collection).filter(Collection.id_user.in_(l_user_info))  # запрос списка доступных слов конкретному пользователю, список id слов
    
    for b in query.all():  
        l_id_user.append(b.id_words)
        
    session.commit()
    
    return len(l_id_user)



if __name__ == "__main__":
    
    print(__name__)
    
    # Проба пера
    add_new_word(eng_word='ddd', rus_word='ддд', i_app_user_id=555)
    add_new_word(eng_word='rrr', rus_word='ррр', i_app_user_id=555)
    add_new_word(eng_word='ddd', rus_word='ддд', i_app_user_id=444)
    
    del_word_for_user(rus_word='ддд', i_app_user_id=555)
    
    select_for_user(i_app_user_id=555)