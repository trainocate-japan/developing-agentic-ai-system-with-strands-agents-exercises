# 演習4: 永続化・Hooks・HITL

**所要時間の目安**: 35分

## この演習でやること

演習3で作成したユーザーサポート担当エージェント（`support_agent`）に、次の3つを追加します。

1. `SnapshotSessionManager`によるセッション永続化（チケット番号をセッションIDとする）
2. `AfterToolCallEvent`に対するHookで、ツール呼び出しの対応履歴を記録する
3. `request_account_unlock`ツールを追加し、`HumanInTheLoop`で承認フローを組み込む

ベースコードファイル: `code/ex4_memory_hitl/agent.py`

このファイルには、演習3の完成形（`receptionist`・`support_agent`・`infra_agent`によるGraph構成）がすでに組み込まれています。`TODO 1`、`TODO 2`、…と番号が振られた場所に、以下の手順のコードを追加しながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

## 手順

### 手順1: セッション管理に必要なクラスをインポートする

`agent.py`の`TODO 1`に、以下を貼り付けます。

```python title="agent.py（TODO 1）"
from strands.session import SnapshotSessionManager
from strands.storage import LocalFileStorage
```

### 手順2: 対応履歴を記録するHookを定義する

まず`TODO 2`に、以下のインポートを貼り付けます。

```python title="agent.py（TODO 2）"
from strands.hooks.events import AfterToolCallEvent
```

続けて`TODO 3`に、Hookのコールバック関数を貼り付けます。

```python title="agent.py（TODO 3）"
def record_interaction_history(event: AfterToolCallEvent) -> None:
    """ツール呼び出しの結果を、対応履歴として記録する。"""
    print(f"[履歴記録] ツール: {event.tool_use['name']} / 結果: {event.result}")
    # 実際の運用では、ここでTICKET_DATAへの追記やログ基盤への送信を行う
```

この関数自体は、まだどのエージェントにも登録されていません。登録は手順4の`create_support_agent`関数の中で行います。

### 手順3: `request_account_unlock`ツールと`HumanInTheLoop`を用意する

まず`TODO 4`に、以下のインポートを貼り付けます。

```python title="agent.py（TODO 4）"
from strands.vended_interventions.hitl import HumanInTheLoop
```

続けて`TODO 5`に、重要操作のツールを貼り付けます。

```python title="agent.py（TODO 5）"
@tool
def request_account_unlock(user_id: str) -> str:
    """指定ユーザーのアカウントロックを解除する(要承認の重要操作)。

    利用者から明確にアカウントロックの解除を求められた場合にのみ使う。
    パスワードを忘れただけでロックはされていない場合は、
    get_password_reset_guideを案内し、このツールは使わない。

    Args:
        user_id: ロックを解除する対象ユーザーのID(例: 社員番号)
    """
    return f"{user_id} のアカウントロックを解除しました。"
```

`request_account_unlock`のdocstringにも、「使う場面」と「使わない場面」の両方を明記しています。重要操作のツールほど、LLMが誤って呼び出さないようにする工夫が効いてきます。

### 手順4: セッション管理・Hook・HITL対応の`support_agent`を作る関数を定義する

`TODO 6`に、3つの機能をまとめて組み込んだエージェントを生成する関数を貼り付けます。

```python title="agent.py（TODO 6）"
def create_support_agent(ticket_id: str) -> Agent:
    """チケットIDをセッションIDとする、永続化・Hook・HITL対応のsupport_agentを生成する。"""
    session_manager = SnapshotSessionManager(
        session_id=ticket_id,
        storage=LocalFileStorage("./sessions/"),
    )

    hitl = HumanInTheLoop(
        allowed_tools=["search_faq", "get_ticket_status", "get_password_reset_guide"],
        ask="stdio",
    )

    new_support_agent = Agent(
        model=model,
        tools=[search_faq, get_ticket_status, get_password_reset_guide, request_account_unlock],
        session_manager=session_manager,
        interventions=[hitl],
        system_prompt=(
            "あなたは社内ITヘルプデスクのユーザーサポート担当です。質問内容に応じて適切なツールを使ってください。"
            "アカウントロックの解除を求められた場合は、request_account_unlockツールを使ってください。"
        ),
    )
    new_support_agent.add_hook(record_interaction_history, AfterToolCallEvent)
    return new_support_agent
```

`session_id`にチケット番号を渡すことで、同じチケットに関するやり取りは同じセッションとして保存・復元されます。`HumanInTheLoop`の`allowed_tools`には、承認なしで実行してよいツールだけを列挙します。`request_account_unlock`は`allowed_tools`に含めていないため、呼び出されようとすると承認待ちで一時停止します。`ask="stdio"`なので、ターミナル上で対話的に承認を求める動作になります。

> **既存の`support_agent`との関係**: ここで定義する`create_support_agent`は、Graph内で使っている`support_agent`とは別に、チケットごとに新しいセッション対応インスタンスを生成するためのものです。本演習の動作確認は、Graphを経由せず、`create_support_agent`が返すエージェントを直接呼び出す形で行います。

### 手順5: 動作確認する

`TODO 7`（`if __name__ == "__main__":`ブロック）に、以下のコードを貼り付けます。

```python title="agent.py（TODO 7）"
# 1回目の問い合わせ
support_agent_1 = create_support_agent("TCK-1001")
result1 = support_agent_1(
    "TCK-1001のVPN接続不可の件で、VPNクライアントの再インストールまで試しましたが繋がりません。"
)
print(result1)

# プロセスの再起動を模して、同じticket_idで新しいインスタンスを作る
support_agent_2 = create_support_agent("TCK-1001")
result2 = support_agent_2("さっきの件、進捗はどうなっていますか?")
print(result2)

# 重要操作(アカウントロック解除)を試す
support_agent_3 = create_support_agent("TCK-9999")
result3 = support_agent_3("山田太郎さん(ユーザーID: user0001)のアカウントロックを解除してください。")
print(result3)
```

ターミナルで実行します。

```bash
python agent.py
```

1つ目と2つ目の呼び出しは、`support_agent_1`と`support_agent_2`という**別のインスタンス**ですが、どちらも`session_id="TCK-1001"`を指定しているため、2つ目の呼び出しでは1つ目の内容を踏まえた応答が返るはずです。これが、プロセスの再起動をまたいだセッション永続化の効果です。3つ目の呼び出しでは、`request_account_unlock`が呼ばれようとするタイミングでターミナルが承認(y/n)を求めてくるので、承認した場合と拒否した場合の両方を試してみてください。また、1つ目・2つ目の呼び出しの中でツールが呼ばれるたびに、`[履歴記録]`から始まる行がコンソールに出力されることも確認してください。

<details>
<summary>模範解答（agent.py 全体）を表示</summary>

```python title="agent.py（完成形）"
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field
from strands.multiagent import GraphBuilder
from strands.session import SnapshotSessionManager
from strands.storage import LocalFileStorage
from strands.hooks.events import AfterToolCallEvent
from strands.vended_interventions.hitl import HumanInTheLoop


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


@tool
def request_account_unlock(user_id: str) -> str:
    """指定ユーザーのアカウントロックを解除する(要承認の重要操作)。

    利用者から明確にアカウントロックの解除を求められた場合にのみ使う。
    パスワードを忘れただけでロックはされていない場合は、
    get_password_reset_guideを案内し、このツールは使わない。

    Args:
        user_id: ロックを解除する対象ユーザーのID(例: 社員番号)
    """
    return f"{user_id} のアカウントロックを解除しました。"


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


def record_interaction_history(event: AfterToolCallEvent) -> None:
    """ツール呼び出しの結果を、対応履歴として記録する。"""
    print(f"[履歴記録] ツール: {event.tool_use['name']} / 結果: {event.result}")
    # 実際の運用では、ここでTICKET_DATAへの追記やログ基盤への送信を行う


def create_support_agent(ticket_id: str) -> Agent:
    """チケットIDをセッションIDとする、永続化・Hook・HITL対応のsupport_agentを生成する。"""
    session_manager = SnapshotSessionManager(
        session_id=ticket_id,
        storage=LocalFileStorage("./sessions/"),
    )

    hitl = HumanInTheLoop(
        allowed_tools=["search_faq", "get_ticket_status", "get_password_reset_guide"],
        ask="stdio",
    )

    new_support_agent = Agent(
        model=model,
        tools=[search_faq, get_ticket_status, get_password_reset_guide, request_account_unlock],
        session_manager=session_manager,
        interventions=[hitl],
        system_prompt=(
            "あなたは社内ITヘルプデスクのユーザーサポート担当です。質問内容に応じて適切なツールを使ってください。"
            "アカウントロックの解除を求められた場合は、request_account_unlockツールを使ってください。"
        ),
    )
    new_support_agent.add_hook(record_interaction_history, AfterToolCallEvent)
    return new_support_agent


if __name__ == "__main__":
    support_agent_1 = create_support_agent("TCK-1001")
    result1 = support_agent_1(
        "TCK-1001のVPN接続不可の件で、VPNクライアントの再インストールまで試しましたが繋がりません。"
    )
    print(result1)

    support_agent_2 = create_support_agent("TCK-1001")
    result2 = support_agent_2("さっきの件、進捗はどうなっていますか?")
    print(result2)

    support_agent_3 = create_support_agent("TCK-9999")
    result3 = support_agent_3("山田太郎さん(ユーザーID: user0001)のアカウントロックを解除してください。")
    print(result3)
```

</details>

## 動作確認チェックリスト

この演習が完了すると、次のことができているはずです。

- [ ] 同じチケット番号で2回に分けて問い合わせを行い、2回目に前回の内容を踏まえた応答が返る
- [ ] ツールが呼ばれるたびに、対応履歴がコンソールに出力される
- [ ] `request_account_unlock`を呼ぶ問い合わせに対し、処理が一時停止し承認を求める
- [ ] 承認した場合はロック解除が実行され、拒否した場合は実行されない

## チャレンジ演習（任意）

Hookで記録した対応履歴を、`TICKET_DATA`の該当チケットに追記する形に拡張してみましょう。

<details>
<summary>チャレンジ演習の模範解答例を表示</summary>

```python
# record_interaction_history関数(TODO 3)を書き換える例
def record_interaction_history(event: AfterToolCallEvent) -> None:
    """ツール呼び出しの結果を、対応履歴として記録する。TICKET_DATAへの追記にも対応。"""
    print(f"[履歴記録] ツール: {event.tool_use['name']} / 結果: {event.result}")

    if event.tool_use["name"] == "get_ticket_status":
        ticket_id = event.tool_use.get("input", {}).get("ticket_id")
        ticket = TICKET_DATA.get(ticket_id)
        if ticket:
            history = ticket.setdefault("history", [])
            history.append(f"[Hook記録] {event.result}")
```

実際の運用では、Hookのコールバックは同期的に呼ばれるため、重い処理(DBへの書き込み等)を行う場合は、応答速度への影響も考慮する必要があります。

</details>

## 次の演習へ

演習5では、これまでエージェントのコードに直接書いていたFAQデータを、MCP(Model Context Protocol)サーバーという外部のナレッジベースから取得する形に拡張します。演習5のベースコード（`code/ex5_mcp/agent.py`）には、この演習の完成形がすでに組み込まれています。
