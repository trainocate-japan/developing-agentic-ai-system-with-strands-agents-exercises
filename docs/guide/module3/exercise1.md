# 演習1: 最小構成エージェント

**所要時間の目安**: 20分

## この演習でやること

社内FAQを検索する`search_faq`ツールを1つだけ持った、最小構成のエージェントを実装します。これが、コース全体を通じて育てていく「社内ITヘルプデスクエージェント」の出発点になります。

ベースコードファイル: `code/ex1_minimal_agent/agent.py`

このファイルを開き、`TODO 1`、`TODO 2`、…と番号が振られた場所に、以下の手順のコードをコピペしながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

## 動作確認チェックリスト

この演習が完了すると、次のことができているはずです。

- [ ] `search_faq`ツールが定義され、FAQデータ（8件）を参照できる
- [ ] エージェントに`search_faq`ツールが登録されている
- [ ] 「パスワードを忘れました」等のFAQに該当する質問に対し、正しい回答が返る
- [ ] FAQに該当しない質問に対し、「該当するFAQが見つかりませんでした」という応答になる
- [ ] `structured_output_model`を使い、`SupportAnswer`で応答を取得できる

## 手順

### 手順1: FAQデータを用意する

`agent.py`の`TODO 1`に、以下のFAQデータを貼り付けます。

```python title="agent.py（TODO 1）"
FAQ_DATA = {
    "VPN": "VPNに接続できない場合は、まず社内ポータルから最新のVPNクライアントを"
           "再インストールし、二要素認証アプリの時刻同期を確認してください。",
    "パスワード": "パスワードを忘れた場合は、社内ポータルの『パスワード再設定』から"
                 "手続きできます。ロックされた場合の解除は情報システム部での対応が必要です。",
    "Wi-Fi": "社内Wi-Fiに接続できない場合は、端末のWi-Fi設定を一度削除し、"
             "社内ポータルに掲載のパスワードで再接続してください。",
    "プリンター": "プリンターが認識されない場合は、社内ポータルの『プリンタードライバー』"
                 "ページから該当機種のドライバーを再インストールしてください。",
    "メール": "社用メールが送受信できない場合は、Webメール版で状況を確認し、"
             "改善しない場合は情報システム部に問い合わせてください。",
    "会議室予約": "会議室予約システムにログインできない場合は、社内SSOのパスワードを"
                 "確認し、改善しない場合は総務部に問い合わせてください。",
    "ソフトウェア": "新しいソフトウェアのインストールには、情報システム部への"
                   "利用申請（社内ポータルの『ソフトウェア利用申請』）が必要です。",
    "PC持ち出し": "社外へのPC持ち出しには、上長承認を得たうえで『PC持ち出し申請』を"
                 "情報システム部に提出してください。",
}
```

### 手順2: `search_faq`ツールを定義する

まず`TODO 2`（ファイル先頭のインポート部分）に、以下を貼り付けます。

```python title="agent.py（TODO 2）"
from strands import tool
```

続けて`TODO 3`に、ツールの定義を貼り付けます。

```python title="agent.py（TODO 3）"
@tool
def search_faq(keyword: str) -> str:
    """社内FAQをキーワードで検索し、よくある質問への回答を返す。

    VPN・パスワード・Wi-Fiなど、社内の手続きややり方に関する
    「どうすればよいか」という問い合わせに使う。

    Args:
        keyword: 検索キーワード（例: VPN, パスワード, Wi-Fi）
    """
    hits = [text for key, text in FAQ_DATA.items() if keyword in key or key in keyword]
    if hits:
        return "\n".join(hits)
    return "該当するFAQが見つかりませんでした。"
```

ここで重要なのは、`search_faq`の**docstring（説明文）の書き方**です。「何のためのツールか」「どんな場面で使うべきか」「引数に何を渡すか」を明記することで、LLMが「今回の質問にはこのツールを使うべきか」を正しく判断できるようになります。

### 手順3: `Agent`を定義する

`TODO 4`に、以下のコードを貼り付けます。

```python title="agent.py（TODO 4）"
agent = Agent(
    model=model,
    tools=[search_faq],
    system_prompt="あなたは社内ITヘルプデスクの担当者です。FAQに関する質問にはsearch_faqツールを使って回答してください。",
)
```

### 手順4: 動作確認する

`TODO 5`（`if __name__ == "__main__":`ブロック）に、以下のコードを貼り付けます。

```python title="agent.py（TODO 5）"
result = agent("パスワードを忘れてしまいました。どうすればいいですか?")
print(result)

result2 = agent("プリンターの色設定がおかしいです。")
print(result2)
```

ターミナルで実行します。

```bash
python agent.py
```

1つ目の問い合わせには、FAQの「パスワード」の内容に基づいた回答が返ることを確認してください。2つ目の問い合わせは、チェックリスト通りであれば「該当するFAQが見つかりませんでした」という応答になるはずです（プリンターのFAQはキーワード「プリンター」で検索されるため、この問い合わせ文だと一致しない点に注目してください）。

### 手順5: 構造化出力に対応する

最後に、応答を`SupportAnswer`という構造化データとして受け取れるようにします。`TODO 6`に、以下のインポートを貼り付けます。

```python title="agent.py（TODO 6）"
from pydantic import BaseModel, Field
```

`TODO 7`に、以下のクラス定義を貼り付けます。

```python title="agent.py（TODO 7）"
class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")
```

最後に、`TODO 5`に書いたコードを、次のように書き換えます。

```python title="agent.py（TODO 5・書き換え）"
result = agent(
    "パスワードを忘れてしまいました。どうすればいいですか?",
    structured_output_model=SupportAnswer,
)
answer = result.structured_output
print(answer.answer)
print(answer.needs_escalation)
```

> **`max_tokens`を忘れずに。** 指定しないと、モデルによっては長大な応答を生成しようとして`MaxTokensReachedException`になることがあります。ベースコードの`model`には、あらかじめ`max_tokens=1024`を設定済みです。

<details>
<summary>模範解答（agent.py 全体）を表示</summary>

```python title="agent.py（完成形）"
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field


model = BedrockModel(
    model_id="<使用するモデルのID>",
    region_name="ap-northeast-1",
    max_tokens=1024,
)


FAQ_DATA = {
    "VPN": "VPNに接続できない場合は、まず社内ポータルから最新のVPNクライアントを"
           "再インストールし、二要素認証アプリの時刻同期を確認してください。",
    "パスワード": "パスワードを忘れた場合は、社内ポータルの『パスワード再設定』から"
                 "手続きできます。ロックされた場合の解除は情報システム部での対応が必要です。",
    "Wi-Fi": "社内Wi-Fiに接続できない場合は、端末のWi-Fi設定を一度削除し、"
             "社内ポータルに掲載のパスワードで再接続してください。",
    "プリンター": "プリンターが認識されない場合は、社内ポータルの『プリンタードライバー』"
                 "ページから該当機種のドライバーを再インストールしてください。",
    "メール": "社用メールが送受信できない場合は、Webメール版で状況を確認し、"
             "改善しない場合は情報システム部に問い合わせてください。",
    "会議室予約": "会議室予約システムにログインできない場合は、社内SSOのパスワードを"
                 "確認し、改善しない場合は総務部に問い合わせてください。",
    "ソフトウェア": "新しいソフトウェアのインストールには、情報システム部への"
                   "利用申請（社内ポータルの『ソフトウェア利用申請』）が必要です。",
    "PC持ち出し": "社外へのPC持ち出しには、上長承認を得たうえで『PC持ち出し申請』を"
                 "情報システム部に提出してください。",
}


@tool
def search_faq(keyword: str) -> str:
    """社内FAQをキーワードで検索し、よくある質問への回答を返す。

    VPN・パスワード・Wi-Fiなど、社内の手続きややり方に関する
    「どうすればよいか」という問い合わせに使う。

    Args:
        keyword: 検索キーワード（例: VPN, パスワード, Wi-Fi）
    """
    hits = [text for key, text in FAQ_DATA.items() if keyword in key or key in keyword]
    if hits:
        return "\n".join(hits)
    return "該当するFAQが見つかりませんでした。"


class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")


agent = Agent(
    model=model,
    tools=[search_faq],
    system_prompt="あなたは社内ITヘルプデスクの担当者です。FAQに関する質問にはsearch_faqツールを使って回答してください。",
)


if __name__ == "__main__":
    result = agent(
        "パスワードを忘れてしまいました。どうすればいいですか?",
        structured_output_model=SupportAnswer,
    )
    answer = result.structured_output
    print(answer.answer)
    print(answer.needs_escalation)
```

</details>

## チャレンジ演習（任意）

1. FAQデータに新しいトピックを1件追加し、正しく検索できることを確認してください。
2. `SupportAnswer`に`category`（問い合わせのカテゴリ）フィールドを追加し、エージェントが適切なカテゴリを判定できるか試してみましょう。

<details>
<summary>チャレンジ演習の模範解答例を表示</summary>

```python
# FAQ_DATAに1件追加する例（TODO 1に追記）
FAQ_DATA["座席予約"] = (
    "フリーアドレス座席の予約は、社内ポータルの『座席予約』から行えます。"
    "当日キャンセルが続く場合は、総務部からの利用停止の対象になることがあります。"
)


# SupportAnswerにcategoryフィールドを追加する例（TODO 7を書き換え）
class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")
    category: str = Field(description="問い合わせのカテゴリ（例: VPN, パスワード, Wi-Fi等）")
```

</details>

## 次の演習へ

演習2では、このエージェントに「チケット状況確認」「パスワードリセット手順案内」の2つのツールを追加し、複数ツールを持つエージェントに拡張します。演習2のベースコード（`code/ex2_multi_tool/agent.py`）には、この演習の完成形がすでに組み込まれています。
