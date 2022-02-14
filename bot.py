from aiogram import Bot, Dispatcher
from aiogram.types import *
from aiogram.utils import executor
import asyncio
import aioschedule
import datetime
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from config import bot_token, admin_id
import sql_work

bot = Bot(bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await bot.send_message(message.chat.id,
                           'Пришли мне ссылку на тайтл с animego.org и я буду уведомлять тебя о новых сериях.\nПроверка происходит каждый день в 09:00 и в 21:00')
    current_url = sql_work.create_profile(message.chat.id)
    if current_url is None:
        await bot.send_message(message.chat.id, 'В данный момент нет отслеживаемого тайтла.')
        await bot.send_message(admin_id, 'Добавлен новый юзер')
    else:
        await bot.send_message(message.chat.id, f'В данный момент отслеживается тайтл по ссылке:\n{current_url}')


@dp.message_handler(content_types=['text'])
async def change_url(message: Message):
    if 'animego.org' in message.text:
        sp = await get_data(message.text)
        if sp is not None:
            episode_name, episode_number, release_date = sp[0], sp[1], sp[2]
            sql_work.edit_url(message.chat.id, message.text)
            await bot.send_message(message.chat.id,
                                   f'{episode_number} "{episode_name}"выйдет {release_date}\nВы будете уведомлены.')
        else:
            await bot.send_message(message.chat.id,
                                   'Нет информации о новых сериях, возможно, сезон закончился.\nПожалуйста, отправьте ссылку на другой тайтл.')
    else:
        await bot.send_message(message.chat.id, 'Произошла ошибка!')


async def check_time():
    for i in sql_work.get_all_data():
        user_id = i[0]
        url = i[1]
        print(user_id)
        print(url)
        months = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
                  'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
        current_date = datetime.date.today()
        sp = await get_data(url=url)
        if sp is not None:
            episode_name, episode_number, release_date = sp[0], sp[1], sp[2]
            ddd = release_date.split(' ')
            day = int(ddd[0])
            month = months.get(ddd[1])
            year = int(ddd[2])
            if current_date.month == month and current_date.day == day - 1 and current_date.year == year:
                await bot.send_message(user_id,
                                       f'Имя: {episode_name}\nНомер эпизода: {episode_number}\nДата релиза: {release_date}\nОтслеживаемый эпизод выходит уже завтра!')
            elif current_date.month == month and current_date.day == day and current_date.year == year:
                await bot.send_message(user_id, f'Эпизод "{episode_name}" выходит уже сегодня, бегом смотреть!\n')
            elif current_date.month >= month and current_date.day > day and current_date.year >= year:
                await bot.send_message(user_id,
                                       'Нет информации о новых сериях, возможно, сезон закончился.\nТайтл снят с отслеживания.')
                sql_work.edit_url(user_id, '')
        else:
            await bot.send_message(user_id,
                                   'Нет информации о новых сериях, возможно, сезон закончился.\nТайтл снят с отслеживания.')
            sql_work.edit_url(user_id, '')


async def get_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
    }
    try:
        async with ClientSession() as session:
            response = await session.get(url=url, headers=headers)
            if response.ok:
                try:
                    soup = BeautifulSoup(await response.text(), 'lxml')
                    last_episode = soup.find('div', class_='col-12 released-episodes-item')
                    episode_number = last_episode.find('div', class_='col-3 col-sm-2 col-md text-truncate').find(
                        'span').text
                    episode_name = last_episode.find('div',
                                                     class_='col-5 col-sm-5 col-md-5 col-lg-5 text-truncate font-weight-bold d-none d-sm-block').text.strip()
                    episode_release = last_episode.find('div',
                                                        class_='col-6 col-sm-3 col-md-3 col-lg-3 text-right text-truncate').find(
                        'a')
                    release_date = episode_release.find('span').text
                    return [episode_name, episode_number, release_date]
                except Exception:
                    return None
    except Exception:
        return None


async def scheduler():
    aioschedule.every().day.at('09:00').do(check_time)
    aioschedule.every().day.at('21:00').do(check_time)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    sql_work.start_base()
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
