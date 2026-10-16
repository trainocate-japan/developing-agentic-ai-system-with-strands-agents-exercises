# 演習3: Graphによる一次切り分け

**所要時間の目安**: 35分

## この演習でやること

問い合わせ内容を「ユーザーサポート担当」と「インフラ運用担当」に振り分ける、Graphパターンのマルチエージェント構成を実装します。受付ノードが問い合わせ内容を判定し、`support`ノードまたは`infra`ノードに動的に分岐します。

ベースコードファイル: `code/ex3_graph/agent.py`

このファイルには、演習2の完成形（`search_faq`・`get_ticket_status`・`get_password_reset_guide`の3ツールを持つエージェント）がすでに組み込まれています。`TODO 1`、`TODO 2`、…と番号が振られた場所に、以下の手順のコードを追加・書き換えしながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

## 手順

### 手順1: 稼働状況データを用意する

`agent.py`の`TODO 1`に、以下の稼働状況データを貼り付けます。

```python title="agent.py（TODO 1）"
SYSTEM_STATUS = {
    "VPN": {"status": "正常", "last_checked": "2026-09-20 09:00"},
    "社内ポータル": {"status": "正常", "last_checked": "2026-09-20 09:00"},
    "メールサーバー": {"status": "一部障害", "last_checked": "2026-09-20 08:30"},
    "会議室予約システム": {"status": "正常", "last_checked": "2026-09-20 09:00"},
}
```

### 手順2: `get_system_status`ツールを定義する

`TODO 2`に、インフラ運用担当が使うツールを貼り付けます。

```python title="agent.py（TODO 2）"
@tool
def get_system_status(system_name: str) -> str:
    """指定された社内システムの稼働状況を確認する。

    「システムが落ちている」「障害ではないか」といった、システムの稼働状況に
    関する問い合わせに使う。一般的な利用者サポート(FAQ・チケット・パスワード)には使わない。

    Args:
        system_name: システム名(例: VPN, メールサーバー, 社内ポータル)
    """
    status = SYSTEM_STATUS.get(system_name)
    if not status:
        return f"システム「{system_name}」の情報は見つかりませんでした。"
    return f"[{system_name}] 状態: {status['status']} (最終確認: {status['last_checked']})"
```

### 手順3: `support_agent`と`infra_agent`を定義する

これまで`agent`という1つの変数にまとめていたエージェントを、役割ごとに分割します。`TODO 3`を、次のように書き換えます。

```python title="agent.py（TODO 3・書き換え）"
support_agent = Agent(
    model=model,
    tools=[search_faq, get_ticket_status, get_password_reset_guide],
    system_prompt="あなたは社内ITヘルプデスクのユーザーサポート担当です。質問内容に応じて適切なツールを使ってください。",
)

infra_agent = Agent(
    model=model,
    tools=[get_system_status],
    system_prompt="あなたは社内ITヘルプデスクのインフラ運用担当です。",
)
```

### 手順4: `receptionist`エージェントを定義する

問い合わせ内容を判定する受付役のエージェントを、`TODO 4`に貼り付けます。

```python title="agent.py（TODO 4）"
receptionist = Agent(
    model=model,
    system_prompt=(
        "あなたは社内ITヘルプデスクの受付担当です。"
        "問い合わせ内容を読み、次のどちらに該当するかを判定してください。\n"
        "- support: パスワード・FAQ・チケット対応状況など、一般的な利用者サポートに関する質問\n"
        "- infra: 社内システムの稼働状況や障害に関する質問\n"
        "回答は「support」または「infra」のどちらか一語のみで答えてください。"
    ),
)
```

受付ノードはツールを持たず、「どちらに振り分けるか」を一語で判定することだけに専念させています。役割を絞ることで、判定の精度を上げやすくなります。

### 手順5: 分岐条件を定義する

まず`TODO 5`（ファイル先頭のインポート部分）に、以下を貼り付けます。

```python title="agent.py（TODO 5）"
from strands.multiagent import GraphBuilder
```

続けて`TODO 6`に、受付ノードの判定結果を見て分岐先を決める関数を貼り付けます。

```python title="agent.py（TODO 6）"
def is_support(state) -> bool:
    classification = str(state.results["receptionist"].result)
    return "support" in classification.lower()


def is_infra(state) -> bool:
    classification = str(state.results["receptionist"].result)
    return "infra" in classification.lower()
```

`GraphBuilder.add_edge`に渡す条件関数は、`GraphState`（ここでは`state`）を受け取り、`True`/`False`を返します。`state.results["receptionist"]`で、受付ノードの実行結果（`NodeResult`）を取得し、`.result`を文字列化することで、受付ノードがLLMとして生成したテキスト（「support」または「infra」）を判定に使えます。

### 手順6: Graphを構築する

`TODO 7`に、3つのノードとその間の遷移を定義するコードを貼り付けます。

```python title="agent.py（TODO 7）"
builder = GraphBuilder()
builder.add_node(receptionist, "receptionist")
builder.add_node(support_agent, "support")
builder.add_node(infra_agent, "infra")
builder.add_edge("receptionist", "support", condition=is_support)
builder.add_edge("receptionist", "infra", condition=is_infra)
builder.set_entry_point("receptionist")

graph = builder.build()
```

`set_entry_point`で、Graphの実行が必ず`receptionist`ノードから始まるように指定しています。`graph`は、Graph全体をまとめて呼び出せる1つの呼び出し可能なオブジェクトです。

### 手順7: 動作確認する

`TODO 8`（`if __name__ == "__main__":`ブロック）に、以下のコードを貼り付けます。コードは`if __name__ == "__main__":`の中に入るため、半角スペース4つでインデント済みです。`TODO`コメントの行を、行頭の空白も含めて選択し、その上から貼り付けてください（インデントの途中や後ろにカーソルを置いて貼ると、1行目だけインデントがずれてエラーになります）。

```python title="agent.py（TODO 8）"
    result = graph("VPNゲートウェイの調子が悪いようです。障害でしょうか?")
    print(result)
```

ターミナルで実行します。

```bash
python agent.py
```

実行結果（`GraphResult`）の中に、`receptionist`ノードと`infra`ノードの両方が実行されたことが確認できれば、分岐は成功です。

### 手順8: サンプル問い合わせ集で分岐精度を確認する

最後に、複数の問い合わせ文を使って、分岐が期待どおりに行われているかをまとめて確認します。`TODO 8`の内容を、次のように書き換えます（先ほど貼り付けたコードを、行頭の空白も含めてまとめて選択し、その上から貼り付けます。こちらも半角スペース4つでインデント済みです）。

```python title="agent.py（TODO 8・書き換え）"
    SAMPLE_INQUIRIES = [
        {"text": "パスワードを忘れてログインできません。", "expected_route": "support"},
        {"text": "VPNゲートウェイが遅くて業務になりません。障害ではないでしょうか。", "expected_route": "infra"},
        {"text": "TCK-1002のチケットの対応状況を教えてください。", "expected_route": "support"},
        {"text": "社内ポータルにアクセスできません。障害が起きていますか?", "expected_route": "infra"},
        {"text": "会議室予約システムにログインできません。パスワードを忘れました。", "expected_route": "support"},
        {"text": "メールサーバーが落ちているようです。確認してもらえますか?", "expected_route": "infra"},
        {"text": "プリンターのドライバーがインストールできません。", "expected_route": "support"},
        {"text": "Wi-Fiの調子が悪いのですが、社内全体の障害でしょうか?", "expected_route": "infra"},
        {"text": "PCの持ち出し申請の手続きを教えてください。", "expected_route": "support"},
        {"text": "会議室予約システムが全社的に落ちていないか確認したいです。", "expected_route": "infra"},
    ]

    for case in SAMPLE_INQUIRIES:
        result = graph(case["text"])
        actual_route = "infra" if "infra" in result.results else "support"
        judge = "OK" if actual_route == case["expected_route"] else "NG"
        print(f"[{judge}] expected={case['expected_route']} actual={actual_route}: {case['text']}")
```

`result.results`は、実際に実行されたノードのIDをキーに持つ辞書です。`"infra"`キーが含まれていれば`infra`ノードまで到達したことがわかるので、これを実際の分岐先として扱い、期待する分岐先（`expected_route`）と突き合わせています。

> **補足**: ここでは`graph`を10件すべてで使い回しているため、各エージェントの会話履歴は件ごとにリセットされません。今回の受付ノードの判定は1件ごとに独立した判定なので大きな影響はありませんが、厳密に分離したい場合は、問い合わせごとに`builder.build()`を呼び直してGraphを作り直す方法もあります。

<details>
<summary>模範解答（agent.py 全体）を表示</summary>

```python title="agent.py（完成形）"
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from strands.multiagent import GraphBuilder


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


SYSTEM_STATUS = {
    "VPN": {"status": "正常", "last_checked": "2026-09-20 09:00"},
    "社内ポータル": {"status": "正常", "last_checked": "2026-09-20 09:00"},
    "メールサーバー": {"status": "一部障害", "last_checked": "2026-09-20 08:30"},
    "会議室予約システム": {"status": "正常", "last_checked": "2026-09-20 09:00"},
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


@tool
def get_system_status(system_name: str) -> str:
    """指定された社内システムの稼働状況を確認する。

    「システムが落ちている」「障害ではないか」といった、システムの稼働状況に
    関する問い合わせに使う。一般的な利用者サポート(FAQ・チケット・パスワード)には使わない。

    Args:
        system_name: システム名(例: VPN, メールサーバー, 社内ポータル)
    """
    status = SYSTEM_STATUS.get(system_name)
    if not status:
        return f"システム「{system_name}」の情報は見つかりませんでした。"
    return f"[{system_name}] 状態: {status['status']} (最終確認: {status['last_checked']})"


class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")


support_agent = Agent(
    model=model,
    tools=[search_faq, get_ticket_status, get_password_reset_guide],
    system_prompt="あなたは社内ITヘルプデスクのユーザーサポート担当です。質問内容に応じて適切なツールを使ってください。",
)

infra_agent = Agent(
    model=model,
    tools=[get_system_status],
    system_prompt="あなたは社内ITヘルプデスクのインフラ運用担当です。",
)

receptionist = Agent(
    model=model,
    system_prompt=(
        "あなたは社内ITヘルプデスクの受付担当です。"
        "問い合わせ内容を読み、次のどちらに該当するかを判定してください。\n"
        "- support: パスワード・FAQ・チケット対応状況など、一般的な利用者サポートに関する質問\n"
        "- infra: 社内システムの稼働状況や障害に関する質問\n"
        "回答は「support」または「infra」のどちらか一語のみで答えてください。"
    ),
)


def is_support(state) -> bool:
    classification = str(state.results["receptionist"].result)
    return "support" in classification.lower()


def is_infra(state) -> bool:
    classification = str(state.results["receptionist"].result)
    return "infra" in classification.lower()


builder = GraphBuilder()
builder.add_node(receptionist, "receptionist")
builder.add_node(support_agent, "support")
builder.add_node(infra_agent, "infra")
builder.add_edge("receptionist", "support", condition=is_support)
builder.add_edge("receptionist", "infra", condition=is_infra)
builder.set_entry_point("receptionist")

graph = builder.build()


if __name__ == "__main__":
    SAMPLE_INQUIRIES = [
        {"text": "パスワードを忘れてログインできません。", "expected_route": "support"},
        {"text": "VPNゲートウェイが遅くて業務になりません。障害ではないでしょうか。", "expected_route": "infra"},
        {"text": "TCK-1002のチケットの対応状況を教えてください。", "expected_route": "support"},
        {"text": "社内ポータルにアクセスできません。障害が起きていますか?", "expected_route": "infra"},
        {"text": "会議室予約システムにログインできません。パスワードを忘れました。", "expected_route": "support"},
        {"text": "メールサーバーが落ちているようです。確認してもらえますか?", "expected_route": "infra"},
        {"text": "プリンターのドライバーがインストールできません。", "expected_route": "support"},
        {"text": "Wi-Fiの調子が悪いのですが、社内全体の障害でしょうか?", "expected_route": "infra"},
        {"text": "PCの持ち出し申請の手続きを教えてください。", "expected_route": "support"},
        {"text": "会議室予約システムが全社的に落ちていないか確認したいです。", "expected_route": "infra"},
    ]

    for case in SAMPLE_INQUIRIES:
        result = graph(case["text"])
        actual_route = "infra" if "infra" in result.results else "support"
        judge = "OK" if actual_route == case["expected_route"] else "NG"
        print(f"[{judge}] expected={case['expected_route']} actual={actual_route}: {case['text']}")
```

</details>

## 動作確認チェックリスト

この演習が完了すると、次のことができているはずです。

- [ ] `support_agent`（ユーザーサポート担当）と`infra_agent`（インフラ運用担当）がそれぞれ定義されている
- [ ] `GraphBuilder`で3つのノード（`receptionist`・`support`・`infra`）が追加され、Graphが構築できている
- [ ] 一般的な問い合わせ（パスワード等）が`support`ノードに正しく分岐する
- [ ] システムの稼働状況に関する問い合わせが`infra`ノードに正しく分岐する
- [ ] サンプル問い合わせ集（10件程度）で分岐精度を確認できる

## チャレンジ演習（任意）

分岐がうまくいかない曖昧な問い合わせ文を1つ作り、なぜ分岐に失敗するのかを考察してください。また、受付ノードの`system_prompt`をどう改善すれば精度が上がりそうか検討してみましょう。

<details>
<summary>チャレンジ演習の模範解答例を表示</summary>

```text
曖昧な問い合わせ文の例:
「VPNのパスワードがわからなくて、繋がらないんですが、これって障害ですか?」

この文は「パスワード」(support寄り)と「VPN」「障害」(infra寄り)の両方の
キーワードを含んでいるため、受付ノードがどちらに分類すべきか迷いやすい。

system_promptの改善例:
「support」と「infra」の判定基準に、具体例をさらに追加する
（例: 「自分のアカウントやパスワードが原因と考えられる場合はsupport、
特定の個人ではなく複数人に影響しそうな社内システム側の問題と考えられる場合はinfra」
のように、判断の観点そのものを明示する）。
```

</details>

## 次の演習へ

演習4では、同じ利用者から複数回にわたって問い合わせが来た場合に、やり取りを会話として永続化する仕組み（Session Manager）と、「アカウントロックの解除」のような重要な操作の前に人間の承認を挟む仕組み（Human-in-the-Loop）を追加します。演習4のベースコード（`code/ex4_memory_hitl/agent.py`）には、この演習の完成形がすでに組み込まれています。
