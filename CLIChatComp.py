import pickle
import openai

# Organization IDの確認: https://platform.openai.com/account/org-settings
# openai.organization = os.getenv('OPENAI_ORGANIZATION')

# APIKEYの作成: https://platform.openai.com/account/api-keys
# openai.api_key = os.getenv('OPENAI_API_KEY')

MODEL = "gpt-3.5-turbo"

CHAT_LOG_FILE = "./chat_log.bin"


def load_chat_log():
    try:
        with open(CHAT_LOG_FILE, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        # チャットのログが存在しない場合
        # AIに送る初期メッセージやシステムメッセージなどを用意して返す
        return [
            {"role": "system", "content": "あなたは歯科理工学分野の教授として、私の質問に答えてください。"},    
        ]


def save_chatlog(chat_log):
    with open(CHAT_LOG_FILE, 'wb') as file:
        pickle.dump(chat_log, file)


def main():
    # AIとのチャットのログが蓄積されていく配列を用意
    chat_log = load_chat_log()

    try:
        while True:
            message = input("Send a message: ")

            # 送信するメッセージをログに追加する
            chat_log.append({"role": "user", "content": message})

            # AIにメッセージを送信する
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=chat_log,
            )

            # AIからの返答をログに追加する
            chat_log.append({"role": "assistant", "content": response.choices[0]['message']['content']})

            # AIからの返答を表示する
            print(response.choices[0]['message']['content'])

            # チャットのログを保存する
            save_chatlog(chat_log)
    except KeyboardInterrupt:
        raise


if __name__ == '__main__':
    main()