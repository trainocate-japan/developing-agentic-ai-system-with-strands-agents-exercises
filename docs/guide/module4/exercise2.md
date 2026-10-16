# 演習2: 複数ツールを持つ単一エージェント

**所要時間の目安**: 25分

## この演習でやること

演習1で作成したエージェントに、`get_ticket_status`（チケット対応状況確認）と`get_password_reset_guide`（パスワードリセット手順案内）の2つのツールを追加し、3つのツールを適切に使い分けられるエージェントに拡張します。

ベースコードファイル: `code/ex2_multi_tool/agent.py`

このファイルには、演習1の完成形（`search_faq`ツール・`SupportAnswer`による構造化出力）がすでに組み込まれています。`TODO 1`、`TODO 2`、…と番号が振られた場所に、以下の手順のコードを追加・書き換えしながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

## 手順

### 手順1: チケットデータを用意する

`agent.py`の`TODO 1`に、以下のチケットデータを貼り付けます。

```python title="agent.py（TODO 1）"
TICKET_DATA = {
    "TCK-1001": {"requester": "山田太郎", "category": "アカウント", "status": "対応中",
                 "summary": "VPN接続不可の問い合わせ", "updated_at": "2026-09-18 10:30"},
    "TCK-1002": {"requester": "佐藤花子", "category": "ハードウェア", "status": "未対応",
                 "summary": "貸与PCのバッテリー不良", "updated_at": "2026-09-19 09:00"},
    "TCK-1003": {"requester": "鈴木一郎", "category": "ソフトウェア", "status": "対応完了",
                 "summary": "業務システムのインストール申請", "updated_at": "2026-09-15 14:20"},
    "TCK-1004": {"requester": "高橋美咲", "category": "アカウント", "status": "対応中",
                 "summary": "メール送受信エラーの調査", "updated_at": "2026-09-19 11:05"},
    "TCK-1005": {"requester": "田中健太", "category": "ネットワーク", "status": "未対応",
                 "summary": "会議室の無線LANが不安定", "updated_at": "2026-09-20 08:45"},
    "TCK-1006": {"requester": "伊藤さくら", "category": "ハードウェア", "status": "対応完了",
                 "summary": "モニターの交換対応", "updated_at": "2026-09-14 16:10"},
}
```

### 手順2: `get_ticket_status`・`get_password_reset_guide`ツールを定義する

`TODO 2`に、2つのツールの定義を貼り付けます。

```python title="agent.py（TODO 2）"
@tool
def get_ticket_status(ticket_id: str) -> str:
    """指定されたチケット番号の対応状況を確認する。

    「チケットはどうなっていますか」「対応状況を教えてください」といった、
    既に起票済みの問い合わせの進捗確認に使う。新規の質問への回答には使わない。

    Args:
        ticket_id: チケット番号(例: TCK-1001)
    """
    ticket = TICKET_DATA.get(ticket_id)
    if not ticket:
        return f"チケット番号 {ticket_id} は見つかりませんでした。"
    return f"[{ticket_id}] ステータス: {ticket['status']} / 概要: {ticket['summary']}"


@tool
def get_password_reset_guide() -> str:
    """パスワードを忘れた、またはロックされた場合のリセット手順を案内する。

    「パスワードを忘れた」「ログインできない」といった質問に使う。
    """
    return ("社内ポータルの「パスワード再設定」から手続きできます。"
            "アカウントがロックされている場合は、情報システム部での本人確認が必要です。")
```

ここでも、docstringの書き方が重要です。`get_ticket_status`のdocstringに「新規の質問への回答には使わない」という一文が入っているのは、`search_faq`との役割の境界をLLMに明確に伝えるためです。ツールが増えるほど、「どんな時に使うか」だけでなく「どんな時に使わないか」まで書くことが、ツール選択の精度に直結します。

### 手順3: `Agent`の定義を3ツール対応に書き換える

`TODO 3`の`agent = Agent(...)`を、次のように書き換えます。

```python title="agent.py（TODO 3・書き換え）"
agent = Agent(
    model=model,
    tools=[search_faq, get_ticket_status, get_password_reset_guide],
    system_prompt="あなたは社内ITヘルプデスクの担当者です。質問内容に応じて適切なツールを使ってください。",
)
```

### 手順4: 動作確認する

`TODO 4`（`if __name__ == "__main__":`ブロック）を、3つのツールをそれぞれ試せる内容に書き換えます。`TODO 4`のコメント行から、その下に最初から書かれているコード（`print(answer.needs_escalation)`の行まで）を、行頭の空白も含めてまとめて選択し、その上から以下のコードを貼り付けてください。コードは`if __name__ == "__main__":`の中に入るため、半角スペース4つでインデント済みです（インデントの途中や後ろにカーソルを置いて貼ると、1行目だけインデントがずれてエラーになります）。

```python title="agent.py（TODO 4・書き換え）"
    result1 = agent(
        "TCK-1001のチケットは今どうなっていますか?",
        structured_output_model=SupportAnswer,
    )
    print(result1.structured_output.answer)

    result2 = agent(
        "パスワードを忘れてしまいました。どうすればいいですか?",
        structured_output_model=SupportAnswer,
    )
    print(result2.structured_output.answer)

    result3 = agent(
        "TCK-9999のチケットの状況を教えてください。",
        structured_output_model=SupportAnswer,
    )
    print(result3.structured_output.answer)
```

ターミナルで実行します。

```bash
python agent.py
```

1つ目は`get_ticket_status`、2つ目は`get_password_reset_guide`、3つ目は存在しないチケット番号に対する`get_ticket_status`の応答（「見つかりませんでした」）が、それぞれ正しく呼ばれることを確認してください。

<details>
<summary>模範解答（agent.py 全体）を表示</summary>

```python title="agent.py（完成形）"
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field


model = BedrockModel(
    model_id="jp.amazon.nova-2-lite-v1:0",
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


TICKET_DATA = {
    "TCK-1001": {"requester": "山田太郎", "category": "アカウント", "status": "対応中",
                 "summary": "VPN接続不可の問い合わせ", "updated_at": "2026-09-18 10:30"},
    "TCK-1002": {"requester": "佐藤花子", "category": "ハードウェア", "status": "未対応",
                 "summary": "貸与PCのバッテリー不良", "updated_at": "2026-09-19 09:00"},
    "TCK-1003": {"requester": "鈴木一郎", "category": "ソフトウェア", "status": "対応完了",
                 "summary": "業務システムのインストール申請", "updated_at": "2026-09-15 14:20"},
    "TCK-1004": {"requester": "高橋美咲", "category": "アカウント", "status": "対応中",
                 "summary": "メール送受信エラーの調査", "updated_at": "2026-09-19 11:05"},
    "TCK-1005": {"requester": "田中健太", "category": "ネットワーク", "status": "未対応",
                 "summary": "会議室の無線LANが不安定", "updated_at": "2026-09-20 08:45"},
    "TCK-1006": {"requester": "伊藤さくら", "category": "ハードウェア", "status": "対応完了",
                 "summary": "モニターの交換対応", "updated_at": "2026-09-14 16:10"},
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


@tool
def get_ticket_status(ticket_id: str) -> str:
    """指定されたチケット番号の対応状況を確認する。

    「チケットはどうなっていますか」「対応状況を教えてください」といった、
    既に起票済みの問い合わせの進捗確認に使う。新規の質問への回答には使わない。

    Args:
        ticket_id: チケット番号(例: TCK-1001)
    """
    ticket = TICKET_DATA.get(ticket_id)
    if not ticket:
        return f"チケット番号 {ticket_id} は見つかりませんでした。"
    return f"[{ticket_id}] ステータス: {ticket['status']} / 概要: {ticket['summary']}"


@tool
def get_password_reset_guide() -> str:
    """パスワードを忘れた、またはロックされた場合のリセット手順を案内する。

    「パスワードを忘れた」「ログインできない」といった質問に使う。
    """
    return ("社内ポータルの「パスワード再設定」から手続きできます。"
            "アカウントがロックされている場合は、情報システム部での本人確認が必要です。")


class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")


agent = Agent(
    model=model,
    tools=[search_faq, get_ticket_status, get_password_reset_guide],
    system_prompt="あなたは社内ITヘルプデスクの担当者です。質問内容に応じて適切なツールを使ってください。",
)


if __name__ == "__main__":
    result1 = agent(
        "TCK-1001のチケットは今どうなっていますか?",
        structured_output_model=SupportAnswer,
    )
    print(result1.structured_output.answer)

    result2 = agent(
        "パスワードを忘れてしまいました。どうすればいいですか?",
        structured_output_model=SupportAnswer,
    )
    print(result2.structured_output.answer)

    result3 = agent(
        "TCK-9999のチケットの状況を教えてください。",
        structured_output_model=SupportAnswer,
    )
    print(result3.structured_output.answer)
```

</details>

## 動作確認チェックリスト

この演習が完了すると、次のことができているはずです。

- [ ] チケットデータ（6件）が`TICKET_DATA`として定義されている
- [ ] `get_ticket_status`ツールが、存在するチケット番号に対して正しいステータスを返す
- [ ] `get_ticket_status`ツールが、存在しないチケット番号に対して適切なメッセージを返す
- [ ] `get_password_reset_guide`ツールが、パスワード関連の質問で正しく呼ばれる
- [ ] 3つのツール（`search_faq`・`get_ticket_status`・`get_password_reset_guide`）が、質問内容に応じて適切に使い分けられている

## チャレンジ演習（任意）

`SlidingWindowConversationManager`を追加し、`window_size`を小さい値（例: 10）に設定した場合と、大きい値（例: 100）に設定した場合とで、複数回のやり取りの後にエージェントの応答がどう変わるか比較してみましょう。

> **`window_size`は、小さくしすぎないでください。** `window_size`は「会話履歴に残すメッセージ数」です。ツールを使う問い合わせ1回あたり、ユーザーの質問・ツール呼び出し・ツールの結果・回答（構造化出力を使うとさらに数件）と、複数のメッセージが履歴に積まれます。1回分のやり取りより小さい値（例: 2）にすると、履歴の先頭が`user`のメッセージではなくなり、`A conversation must start with a user message`という`ValidationException`になることがあります。

<details>
<summary>チャレンジ演習の模範解答例を表示</summary>

まず、ファイル先頭のインポートに、次の1行を追加します（既存の`from ... import ...`の行の下に追記）。

```python
from strands.agent.conversation_manager import SlidingWindowConversationManager
```

次に、`TODO 3`の`Agent`の定義を、`conversation_manager`付きに書き換えます。

```python
agent = Agent(
    model=model,
    tools=[search_faq, get_ticket_status, get_password_reset_guide],
    conversation_manager=SlidingWindowConversationManager(window_size=10),
    system_prompt="あなたは社内ITヘルプデスクの担当者です。質問内容に応じて適切なツールを使ってください。",
)
```

最後に、`TODO 4`（`if __name__ == "__main__":`ブロック）を、複数の質問を連続で送り、最初の質問の内容を最後に尋ねるコードに書き換えます。履歴に残っているメッセージ数も表示して、`window_size`の効果を確認できるようにします。

```python
    questions = [
        "TCK-1001のチケットは今どうなっていますか?",
        "パスワードを忘れてしまいました。どうすればいいですか?",
        "TCK-1002のチケットの状況を教えてください。",
        "VPNに接続できない場合はどうすればいいですか?",
        "TCK-1003のチケットの状況を教えてください。",
        "Wi-Fiに接続できない場合はどうすればいいですか?",
        "TCK-1004のチケットの状況を教えてください。",
        "プリンターが認識されない場合はどうすればいいですか?",
        "TCK-1005のチケットの状況を教えてください。",
        "最初にお尋ねしたチケットの番号と、その状況をもう一度教えてください。",
    ]
    for question in questions:
        result = agent(question, structured_output_model=SupportAnswer)
        print(f"Q: {question}")
        print(f"A: {result.structured_output.answer}")
        print(f"（履歴のメッセージ数: {len(agent.messages)}）")
        print("-" * 40)
```

`window_size=10`で実行すると、履歴のメッセージ数が10前後で頭打ちになり、最後の質問の時点では最初のやり取りが履歴から外れています。そのため、最初のチケット（`TCK-1001`）ではなく、履歴に残っている直近のチケット（`TCK-1005`など）の状況を答えたり、「どのチケットですか?」と確認を求めたりする応答になります。忘れたことを自覚せずに、もっともらしい別の答えを返す点にも注目してください。`window_size=100`に変えて実行し直すと、メッセージ数が増え続け、最初のやり取りが履歴に残るため、「TCK-1001」とその状況（対応中）を答えられることを確認してください。

> **履歴に残るメッセージ数は、問い合わせの内容によって変わります。** ツールを呼ぶ問い合わせほど、1回あたりのメッセージ数が多くなります。質問が少ないと、`window_size=10`でも最初のやり取りが残ってしまうことがあるため、ここでは10回の質問を送っています。

</details>

## 次の演習へ

演習3では、社内ヘルプデスクに「社内システムの稼働状況確認」という、性質の異なる問い合わせが増えてきたことを受けて、1つのエージェントにツールを積み増すのではなく、役割ごとにエージェントを分割し、マルチエージェント構成（Graph）に拡張します。演習3のベースコード（`code/ex3_graph/agent.py`）には、この演習の完成形がすでに組み込まれています。
