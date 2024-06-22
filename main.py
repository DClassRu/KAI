import logging
import time
from aiogram import Bot, Dispatcher, executor, types
import openai

bot_token = ''
OPENAI_TOKEN = ''

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


messages = {}
openai_client = openai.AsyncOpenAI(api_key=OPENAI_TOKEN)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    try:
        username = message.from_user.username
        name = message.from_user.first_name
        messages[username] = []
        messages[username].append({"role": "system", "content":f"Тебя зовут Кай, ты школьный бот-помощник школьной метавселенной DClass школы №72. Твоя задача - отвечать на вопросы школьников, помогать им по учёбе. Обращайся к данному пользователю по имени {name}"})
        await message.answer(f"Привет, {name}!\nМеня зовут Кай, я цифровой помощник метавселенной DClass школы №72 г.Казани, приятно познакомиться!\nТы можешь обращаться ко мне по любым вопросам, я обязательно помогу тебе!\n\nДля того чтобы сменить тему диалога используй команду /newtopic")
    except Exception as e:
        logging.error(f'Error in start_cmd: {e}')

@dp.message_handler(commands=['newtopic'])
async def new_topic_cmd(message: types.Message):
    try:
        userid = message.from_user.username
        message[str(userid)] = []
        await message.reply('Так и быть - начинаем новую тему!', parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')


@dp.message_handler()
async def echo_msg(message: types.Message):
    try:
        user_message = message.text
        userid = message.from_user.username

        if userid not in messages:
            messages[userid] = []
        messages[userid].append({"role": "user", "content": user_message})
        messages[userid].append({"role": "user", "content": f"chat: {message.chat} Сейчас {time.strftime('%d/%m/%Y %H:%M:%S')} user: {message.from_user.first_name} message: {message.text}"})
        logging.info(f'{userid}: {user_message}')

        should_respond = not message.reply_to_message or message.reply_to_message.from_user.id == bot.id

        if should_respond:
            processing_message = await message.reply(
            '⌛',
            parse_mode='Markdown')

            await bot.send_chat_action(chat_id=message.chat.id, action="typing")

            completion = openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=messages[userid],
                max_tokens=2500,
                temperature=0.7,
                frequency_penalty=0,
                presence_penalty=0,
                user=userid
            )
            chatgpt_response = completion.choices[0]['message']

            messages[userid].append({"role": "assistant", "content": chatgpt_response['content']})
            logging.info(f'Кай ответил: {chatgpt_response["content"]}')

            await message.reply(chatgpt_response['content'])

            await bot.delete_message(chat_id=processing_message.chat.id, message_id=processing_message.message_id)

    except Exception as ex:
        # не работает
    if 'context_length_exceeded' in str(ex):
            await message.reply(
                '* * * У бота закончилась память, пересоздаем диалог... * * *',
                parse_mode='Markdown')
            await new_topic_cmd(message)
            await echo_msg(message)


if __name__ == '__main__':
    executor.start_polling(dp)  
