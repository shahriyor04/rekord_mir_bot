import asyncio
import random
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.utils import executor
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

API_TOKEN = '6773167505:AAF_RR7iQgA-T7uvXTkDoJcxOEZ79G1tOAI'
from aiogram.dispatcher.filters.state import StatesGroup, State

bot = Bot(API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

storage = MemoryStorage()
dp.storage = storage
DATABASE_URL = 'sqlite:///food.db'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Users(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)

    fullname = Column(String)
    address = Column(String)
    phone_number = Column(Integer)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class Forms(StatesGroup):
    fullname = State()
    address = State()
    phone_number = State()


def order_keyboart():
    ikm = InlineKeyboardMarkup()
    ikm.add(InlineKeyboardButton("o'chirish", callback_data="o'chirish"))
    return ikm


def save_order_to_database(db_session: Session, data):
    order = Users(fullname=data['fullname'], address=data['address'], phone_number=data['phone_number'])
    db_session.add(order)
    db_session.commit()


def inline_button():
    channel_url = InlineKeyboardButton('Kanalimiz', url='https://t.me/rekord_m1r')
    check = InlineKeyboardButton('Tekshirish', callback_data='subdone')
    markab = InlineKeyboardMarkup(row_width=1).add(channel_url, check)
    return markab


#
@dp.callback_query_handler(state='*')
async def check_sub(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'subdone':
        check_sub_channel = await bot.get_chat_member(chat_id=-1001995642741, user_id=callback.from_user.id)

        if check_sub_channel['status'] != 'left':
            await callback.message.answer('Kanalga azo bo''lganingiz uchun raxmat!')
            # Check if user is already in a conversation
            async with state.proxy() as data:
                if 'fullname' not in data:
                    await callback.message.answer("Iltimos ismingizni kiriting: Shablon 'Mahmudjonov Valijon'")
                    await Forms.fullname.set()
                else:
                    await callback.message.answer("Siz allaqachon kanalga azosiz va ma'lumotlaringiz kiritilgan.")
        else:
            await callback.message.answer("Botdan foydalanish uchun kanalimizga azo bo'ling",
                                          reply_markup=inline_button())


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    check_sub_channel = await bot.get_chat_member(chat_id=-1001995642741, user_id=message.from_user.id)

    if check_sub_channel['status'] != 'left':
        await message.answer('Kanalga azo bo''lganingiz uchun raxmat!')
        # Check if user is already in a conversation
        async with state.proxy() as data:
            if 'fullname' not in data:
                await message.answer("Iltimos ismingizni kiriting: Shablon 'Mahmudjonov Valijon'")
                await Forms.fullname.set()
            else:
                await message.answer("Siz allaqachon kanalga azosiz va ma'lumotlaringiz kiritilgan.")
    else:
        await message.answer("Botdan foydalanish uchun kanalimizga azo bo'ling", reply_markup=inline_button())


@dp.message_handler(state=Forms.fullname)
async def process_fullname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['fullname'] = message.text
    await Forms.next()
    await message.answer("Iltimos manzilingizni kiriting: Shablon 'Sherobod tumani, Qizil olma MFY, Jartepa qishloq:85")


@dp.message_handler(state=Forms.address)
async def process_fullname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['address'] = message.text
    await Forms.next()
    await message.answer("Telefon nomeringizni kiriting: Shablon '91 360 69 43'")


@dp.message_handler(state=Forms.phone_number)
async def process_address(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        phone_number = message.text.strip()

        if phone_number.isdigit() and len(phone_number) == 9:
            data['phone_number'] = phone_number
            order_info = (
                f"Isim Familiya: {data['fullname']}\n"
                f"Address : {data['address']}\n"
                f"Telefon nomer: +998 {data['phone_number']}\n"
            )

            admin_id = 944676439
            await bot.send_message(admin_id, f"New order:\n\n{order_info}", reply_markup=order_keyboart())
            await message.answer(
                "Habaringiz adminga jo'natildi tez orada adminlarimiz siz bilan bog'lanishadi")
            await state.finish()
            db_session = Session()
            save_order_to_database(db_session, data)
            db_session.close()
        else:

            await message.reply("Noto'g'ri telefon raqami! Raqamlika va uzunligi 9 ga teng bo'lishi kerak.")


@dp.callback_query_handler(lambda query: query.data.startswith("o'chirish"))
async def delete_message(query: types.CallbackQuery):
    chat_id = query.message.chat.id
    await bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
    await bot.send_message(chat_id=chat_id, text=f' Buyurtma o''chirildi')


@dp.message_handler(commands=['users'])
async def count_users(message: types.Message):
    session = Session()
    total_users = session.query(Users).count()
    await message.reply(f"🤖 Botga malumot qoldirgan userlar soni {total_users} \n")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
