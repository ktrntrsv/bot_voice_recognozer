from urllib.request import urlretrieve
import speech_recognition as sr
from pydub import AudioSegment
from termcolor import colored

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id


def checking_reply_forward(msg, vk_session):
    messages = []
    print("Checking reply forward")
    if "reply_message" in msg:
        print("Replied message.")
        msg = msg['reply_message']
        # pprint(msg)
        return checking_reply_forward(msg, vk_session)
    if 'fwd_messages' in msg and msg['fwd_messages']:
        print("Forwarded message.")
        # pprint(msg['fwd_messages'][0])
        for message in msg['fwd_messages']:
            print(len(msg["fwd_messages"]))
            print("MESSAGE")
            print(msg['fwd_messages'])
            print(message)
            if not message:
                pass
            # pprint(message)
            messages.append(checking_reply_forward(message, vk_session))
        return messages
    print("Nothing!")
    return msg


def get_token():
    with open("token", "r") as f:
        return f.readline()


def downloading(url):
    print("Downloading.")
    dest = "vk_message.mp3"
    urlretrieve(url, dest)
    return dest


def converting(src: str):
    print("Converting.")
    src = src
    dst = f"{src[-3]}wav"

    sound = AudioSegment.from_mp3(src)
    sound.export(dst, format="wav")
    return dst


def recognizing(file_wav):
    print("Recognizing.")
    audio_file = file_wav
    r = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)  # read the entire audio file

    try:
        text = r.recognize_google(audio, language="ru-RU").capitalize()
    except sr.UnknownValueError:
        text = "Strange things happen here :("

    print(f"Text is \"{text}\".")
    return text


def vk_message_sending(vk, event, text: str):
    print(f"Sending vk message. Text: {text}")
    vk.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=text
    )


def main():
    vk_session = vk_api.VkApi(token=get_token())
    vk = vk_session.get_api()
    long_poll = VkLongPoll(vk_session)

    print(colored("Starting", "green"))

    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

            message_data = vk_session.method(
                'messages.getById',
                {'message_ids': {event.message_id}}
            )["items"][0]

            messages_data = checking_reply_forward(message_data, vk_session)

            for message_data in messages_data:
                if isinstance(message_data, str):  # if a message wasn't forward
                    message_data = messages_data

                link_mp3 = message_data["attachments"]
                if not link_mp3 or all(link_mp3[i]["type"] != "audio_message" for i in range(len(link_mp3))):
                    vk_message_sending(vk, event, "Send me audio message. \n"
                                                  "(If you replied the audio message, please, forward it)")
                    continue
                try:
                    link_mp3 = link_mp3[0]["audio_message"]["link_mp3"]
                    file_mp3 = downloading(link_mp3)
                    file_wav = converting(file_mp3)
                    text = recognizing(file_wav)
                    vk_message_sending(vk, event, text)
                except Exception as ex:
                    print(ex)
                    vk_message_sending(vk, event, "Sorry, something went wrong, i need some rest :(")

                if messages_data == message_data:
                    break  # if a message wasn't forward


            print("Done.\n\n")


if __name__ == '__main__':
    main()
