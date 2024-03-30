import telebot
from telebot import types
import moviepy.editor as mp
import os

API_TOKEN = 'токенсюда' 

bot = telebot.TeleBot(API_TOKEN)

def clean_up(*file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Приветствую! 🙌n"
        "Здесь ты можешь преобразовать свои видео в видеокружки! 🎥➡️🔵nn"
        "Отправляй мне любое видео, и я создам из него кружок. Однако если видео будет длиннее одной минуты, "
        "видеокружок будет содержать только первые 60 секунд из-за ограничений Telegram. ⏱nn"
        "По всем вопросам обращайся к разработчику @pizzaway! 👨‍💻✨"
    )
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Привет! Отправь мне видео, и я конвертирую его в видеокружок. 🎥🔄🙂. Если что, жми /help')

@bot.message_handler(content_types=['video'])
def handle_video(message):
    file_id = message.video.file_id
    video_file_path = f'video_{file_id}.mp4'
    video_note_path = f'video_note_{file_id}.mp4'
    
    try:
        msg_download = bot.send_message(message.chat.id, 'Скачиваю видео... ⏳')
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(video_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.delete_message(chat_id=message.chat.id, message_id=msg_download.message_id)

        msg_convert = bot.send_message(message.chat.id, 'Конвертирую видео в кружок... 🔄')
        clip = mp.VideoFileClip(video_file_path)
        min_dimension = min(clip.size)
        clip_circular = clip.crop(width=min_dimension, height=min_dimension, x_center=clip.w/2, y_center=clip.h/2)
        clip_circular.write_videofile(video_note_path, codec='libx264', audio_codec='aac', threads=1)
        clip.close()
        bot.delete_message(chat_id=message.chat.id, message_id=msg_convert.message_id)

        msg_send = bot.send_message(message.chat.id, 'Отправляю кружочек... 📤')
        with open(video_note_path, 'rb') as video:
            bot.send_video_note(message.chat.id, video, duration=message.video.duration)
        bot.delete_message(chat_id=message.chat.id, message_id=msg_send.message_id)

        bot.send_message(message.chat.id, 'Разработчик: @pizzaway')

    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка при обработке вашего видео 😥')
        print(e)
    finally:
        clean_up(video_file_path, video_note_path)

bot.infinity_polling()