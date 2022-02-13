from aiogram import Bot, Dispatcher
from aiogram.types import *
from aiogram.utils import executor
import asyncio
import aioschedule
import datetime
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from config import bot_token, start_url, admin_id

bot = Bot(bot_token)
dp = Dispatcher(bot)

url = start_url


@dp.message_handler(commands=['start'])
async def start(message: Message):
    if message.chat.id == admin_id:
        await bot.send_message(admin_id,
                               'Пришли мне ссылку на тайтл с animego.org и я буду уведомлять тебя о новых сериях.\nПроверка происходит каждый день в 09:00')
        if url == '':
            await bot.send_message(admin_id, 'В данный момент нет отслеживаемого тайтла.')
        else:
            await bot.send_message(admin_id, f'В данный момент отслеживается тайтл по ссылке:\n{url}')
    else:
        await message.reply('access denied :)')


@dp.message_handler(content_types=['text'])
async def change_url(message: Message):
    if message.chat.id == admin_id and 'animego.org' in message.text:
        global url
        url = message.text
        await bot.send_message(message.chat.id, 'Ожидаемый тайт упешно изменен!')
        await check_time()
    else:
        await bot.send_message(message.chat.id, 'Произошла ошибка!')


async def check_time():
    global url
    if url != '':
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
                await bot.send_message(admin_id,
                                       f'Name: {episode_name}\nEpisode number: {episode_number}\nRelease date: {release_date}\nEpisode comes out tomorrow!!!')
            elif current_date.month == month and current_date.day == day and current_date.year == year:
                await bot.send_message(admin_id, f'Эпизод "{episode_name}" выходит уже сегодня, бегом смотреть!\n')
            elif current_date.month >= month and current_date.day > day and current_date.year >= year:
                await bot.send_message(admin_id,
                                       'Нет информации о новых сериях, возможно, сезон закончился.\nТайтл снят с отслеживания.')
                url = ''
            else:
                await bot.send_message(admin_id,
                                       f'Следующий эпизод выйдет {release_date}\nВы будете уведомлены о новых сериях.')
        else:
            await bot.send_message(admin_id,
                                   'Нет информации о новых сериях, возможно, сезон закончился.\nТайтл снят с отслеживания.')
            url = ''


async def get_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
    }
    try:
        async with ClientSession() as session:
            response = await session.get(url=url, headers=headers)
            if response.ok:
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
    except Exception as ex:
        print(f'{ex}')
        return None


async def scheduler():
    aioschedule.every().day.at('14:21').do(check_time)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
