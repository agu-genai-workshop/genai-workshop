import base64
import json
import queue
import threading
import tkinter
import uuid
from io import BytesIO
from tkinter import scrolledtext

import openai
from PIL import Image

# Organization IDの確認: https://platform.openai.com/account/org-settings
# openai.organization = os.getenv('OPENAI_ORGID')

# APIKEYの作成: https://platform.openai.com/account/api-keys
# openai.api_key = os.getenv('OPENAI_APIKEY')


MODEL = "gpt-4"


class App(tkinter.Frame):
    def __init__(self, master=None, thread_event=None, send_queue=None, response_queue=None):
        super().__init__(master)
        self.pack(fill=tkinter.BOTH, expand=True)

        # チャットログを格納していく配列を作成しておく
        self.chat_log = [
            {"role": "system", "content": "あなたは歯科理工学分野の教授として、私の質問に答えてください。"}
        ]

        self.thread_event = thread_event
        self.send_queue = send_queue
        self.response_queue = response_queue

        # チャットログを表示するテキストエリアを作成
        self.text_area = scrolledtext.ScrolledText(
            self,
            wrap=tkinter.WORD,  # 単語単位で改行
            width=80,
            # height=20
        )

        # テキストエリアの編集を無効化
        # state=tkinter.DISABLEDすると内容書き込みのたびにNORMALとDISABLEDを切り替える必要がある
        # そこで、<Key>イベントを捕捉して、キー入力を無視するようにする
        self.text_area.bind("<Key>", lambda e: "break")
        self.text_area.pack(fill=tkinter.BOTH, expand=True, anchor=tkinter.NW)

        # 送信するメッセージを入力するテキストエリアを作成
        self.input_message_var = tkinter.StringVar()
        self.chat_message_input_area = tkinter.Entry(
            self,
            bg="#ffffff",
            fg="#000000",
            insertbackground='black',
            textvariable=self.input_message_var
        )
        self.chat_message_input_area.bind('<Return>', self.send_message)
        self.chat_message_input_area.pack(fill=tkinter.X, expand=True, anchor=tkinter.S)

        # AIからのレスポンスがあったら、テキストエリアに表示する監視を開始
        self.master.after(1000, self.update_response)

    def update_response(self):
        # AIからのレスポンスがないかを確認
        if not self.response_queue.empty():
            # レスポンスがあるなら、文脈保存用のチャットログに追加し、テキストエリアに表示する
            response = self.response_queue.get()
            self.chat_log.append(response)
            self.text_area.insert(tkinter.END, "AI > " + response['content'] + '\n')

        self.master.after(1000, self.update_response)

    def send_message(self, event):
        # 入力されている文字列をウィジェットから取得してから、入力欄を空にする
        message = self.input_message_var.get()
        self.input_message_var.set("")

        # 送信する型にくるんで、チャットログの末尾に追加する
        self.chat_log.append({"role": "user", "content": message})
        self.text_area.insert(tkinter.END, "You > " + message + '\n')

        # スレッドに現在のCHAT_LOGを渡して、待機状態スレッドを再開させる
        self.send_queue.put(self.chat_log)
        self.thread_event.set()


def chat_comp_task(event, stop, chat_message_queue, response_queue):
    while not stop:
        event.wait()
        event.clear()

        chat_log = chat_message_queue.get()
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=chat_log,
            function_call="auto",
            functions=[
                {
                    "name": "create_image",
                    "description": "英語の文字列のプロンプトから画像生成を行い、保存したファイル名を返す関数。"
                                   "戻り値はJSON形式でfilenameというフィールドの中身にファイル名が入っている。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input_prompt": {
                                "type": "string",
                                "description": "DALLEのプロンプトとして渡す文字列。英語で表現されていなければいけない。"
                            },
                        },
                        "required": ["input_prompt"]
                    }
                },
                {
                    "name": "speach_to_text",
                    "description": "音声ファイルをテキストに変換する関数。ファイル名を引数に取り、音声からの文字起こしを行う。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "音声ファイルのファイル名。"
                            }
                        }
                    },
                    "required": ["filename"]
                }
            ]
        )

        # 返答内容を確認し、Function callが要求されていたら関数の処理を行う
        if response.choices[0]['message'].get('function_call'):
            function_name = response.choices[0]['message']['function_call']['name']
            arguments = json.loads(response.choices[0]['message']['function_call']["arguments"])

            func = globals()[function_name]
            function_response = func(**arguments)

            chat_log.append({"role": "function", "name": function_name, "content": function_response})

            second_response = openai.ChatCompletion.create(
                model=MODEL,
                messages=chat_log,
            )

            response_queue.put(second_response.choices[0]['message'])
        else:
            # AIからの返答内容を返答キューに追加
            response_queue.put(response.choices[0]['message'])


def create_image(input_prompt):
    # DALLEのプロンプトを渡して画像を生成する関数
    response = openai.Image.create(
        prompt=input_prompt,
        n=1,
        size="256x256",
        response_format="b64_json",
    )

    for data in response['data']:
        img_raw = base64.b64decode(data['b64_json'])
        img = Image.open(BytesIO(img_raw))
        image_filename = str(uuid.uuid4())
        img.save(image_filename + '.png')
        return json.dumps({"filename": image_filename + '.png'})


def speach_to_text(filename):
    # 音声ファイルをテキストに変換する関数
    audio_file = open(filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    with open(f'./transcribed.txt', 'w+') as file:
        file.write(transcript['text'])

    return json.dumps({"text": transcript['text']})


def main():
    thread_event = threading.Event()
    send_queue = queue.Queue()
    response_queue = queue.Queue()
    stop = False

    thread = threading.Thread(target=chat_comp_task, args=(thread_event, stop, send_queue, response_queue,))
    thread.start()

    root = tkinter.Tk()
    root.geometry('500x400')

    app = App(master=root, thread_event=thread_event, send_queue=send_queue, response_queue=response_queue)
    app.mainloop()


if __name__ == '__main__':
    main()
