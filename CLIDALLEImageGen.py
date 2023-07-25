import openai
import base64
from PIL import Image
from io import BytesIO

# Organization IDの確認: https://platform.openai.com/account/org-settings
# openai.organization = os.getenv('OPENAI_ORGID')

# APIKEYの作成: https://platform.openai.com/account/api-keys
# openai.api_key = os.getenv('OPENAI_APIKEY')


def main():
    number_of_images = int(input("何枚の画像を生成しますか？: "))

    while True:
        input_prompt = input("send a situation: ")

        try:
            response = openai.Image.create(
                prompt=input_prompt,
                n=number_of_images,
                size="1024x1024",
                response_format="b64_json",
            )

            for data in response['data']:
                img_raw = base64.b64decode(data['b64_json'])
                img = Image.open(BytesIO(img_raw))
                img.show()

        except KeyboardInterrupt:
            raise


if __name__ == '__main__':
    main()
