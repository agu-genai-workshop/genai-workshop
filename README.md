# 人工知能ワークショップ

教員のための人工知能ワークショップ

〜人工知能との共同作業による教育・研究効率の向上〜


## Organization ID の確認と API Keyの確認方法

[Organization IDの確認 \
https://platform.openai.com/account/org-settings](https://platform.openai.com/account/org-settings)

[API KEYの作成 \
https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)



## ThonnyのAPIキー設定
Thonny → Settings... → General

Environment variables: に以下を追加
```
OPENAI_ORGANIZATION=org-*************************
OPENAI_API_KEY=sk-*************************
```


## CLIChatComp

APIを使ったChatGPT


## CLIDALLEImageGen

DALL•Eによる画像生成


## talktoimage

Function callingの実践
チャット入力欄と会話のログをtkinterで表示し

チャット内容に応じて

- DALL•Eによる画像生成
- 音声ファイルからの文字起こし

を自動で判断して行う
