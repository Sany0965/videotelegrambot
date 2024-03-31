import telebot
import moviepy.editor as mp
import os
import time

API_TOKEN = 'API_TOKEN'  # Ваш API токен

bot = telebot.TeleBot(API_TOKEN)

# Идентификатор разработчика
DEVELOPER_ID = СЮДАID

# Хранилище данных о пользователях
users_data = {}

def clean_up(*file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

@bot.message_handler(commands=['help'])
def send_help(message):
    user_name = message.from_user.first_name if message.from_user.first_name else "пользователь"
    help_text = (
        f"Привет, {user_name}! 🙌\n"
        "Здесь ты можешь преобразовать свои видео в видеокружки! 🎥➡️🔵\n\n"
        "Отправляй мне любое видео, и я создам из него кружок. Однако если видео будет длиннее одной минуты, "
        "Видеокружок Не будет создан, из-за ограничений Telegram ⏱\n\n"
        "По всем вопросам обращайся к разработчику @pizzaway! 👨‍💻✨"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name if message.from_user.first_name else "пользователь"
    if message.from_user.id not in users_data:
        users_data[message.from_user.id] = {'username': message.from_user.username}
    bot.reply_to(message, f'Привет, {user_name}! Отправь мне видео, и я конвертирую его в видеокружок. 🎥🔄🙂. Если что, жми /help')

@bot.message_handler(content_types=['video'])
def handle_video(message):
    if message.video.duration > 60:
        bot.reply_to(message, "Извините, видео не должно длиться более 60 секунд! Пожалуйста, отправьте короткое видео.")
        return

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
        
        start_time = time.time()  # Запоминаем время начала обработки видео
        clip = mp.VideoFileClip(video_file_path)
        min_dimension = min(clip.size)
        clip_circular = clip.crop(width=min_dimension, height=min_dimension, x_center=clip.w/2, y_center=clip.h/2)
        clip_circular.write_videofile(video_note_path, codec='libx264', audio_codec='aac', threads=1)
        clip.close()
        processing_time = round(time.time() - start_time, 2)  # Вычисляем время обработки видео
        bot.delete_message(chat_id=message.chat.id, message_id=msg_convert.message_id)

        with open(video_note_path, 'rb') as video:
            sent_message = bot.send_video_note(message.chat.id, video, duration=message.video.duration)
        
        bot.send_message(message.chat.id, f'Время Обработки - {processing_time} сек.', reply_to_message_id=sent_message.message_id)
        
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка при обработке вашего видео 😥. Пришлите пожалуйста другое видео, или пришлите это видео с соотношением 1:1')
        print(e)
    finally:
        clean_up(video_file_path, video_note_path)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "Извините, Вы прислали фотографию, пожалуйста пришлите видео для конвертации. 😕")

@bot.message_handler(commands=['sms'])
def start_message_distribution(message):
    if message.from_user.id == DEVELOPER_ID:
        bot.send_message(DEVELOPER_ID, "Введите текст для рассылки:")
        bot.register_next_step_handler(message, handle_message_input)
    else:
        bot.send_message(message.chat.id, "Эта команда доступна только разработчикам.")

def handle_message_input(message):
    input_text = message.text
    if input_text:
        distribute_message(input_text)
    else:
        bot.send_message(DEVELOPER_ID, "Введенный текст пустой. Пожалуйста, повторите попытку.")

def distribute_message(message_text):
    delivered_users = []

    for user_id, user_data in users_data.items():
        if user_id != DEVELOPER_ID:
            try:
                bot.send_message(user_id, f"[Рассылка от админа] - {message_text}")
                delivered_users.append(f"@{user_data.get('username', f'Пользователь_{user_id}')}")
            except telebot.apihelper.ApiException as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    delivered_text = (f"Рассылка завершена. Сообщение успешно доставлено пользователям: "
                      f"{', '.join(delivered_users)}" if delivered_users
                      else "Рассылка завершена. Не удалось доставить сообщение ни одному пользователю.")
    bot.send_message(DEVELOPER_ID, delivered_text)

bot.infinity_polling()
