# 演習⑤: MCPサーバーへの接続

**対応モジュール**: 第7章　MCPによる連携設計
**所要時間の目安**: 20分

## この演習でやること

配布される社内ナレッジベースMCPサーバー（`kb_mcp_server.py`）に接続し、`search_kb`・`get_article`という2つのツールを、`support_agent`に追加します。この演習は軽量な位置づけで、MCPサーバー自体の実装は不要です。配布されたサーバーに接続し、動作を確認することが目的です。

ベースコードファイル: `code/ex5_mcp/agent.py`

配布アセット: `code/ex5_mcp/kb_mcp_server.py`（このファイルはすでに完成しています。変更は不要です）

`kb_mcp_server.py`を`agent.py`と同じディレクトリに置いてください。`agent.py`の`TODO 1`、`TODO 2`、…と番号が振られた場所に、以下の手順のコードを追加・書き換えしながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

## 動作確認チェックリスト

この演習が完了すると、次のことができているはずです。

- [ ] `MCPClient`を使い、`kb_mcp_server.py`にstdioトランスポートで接続できる
- [ ] `MCPClient`のインスタンスを`Agent`の`tools=[...]`に直接渡し、接続エラーなくエージェントが動作する
- [ ] 「経費精算のやり方を教えてください」のような、ローカルのFAQデータには含まれない質問に対し、MCP経由の`search_kb`が呼ばれ、正しい回答が返る
- [ ] ローカルのFAQ（`search_faq`）とMCP経由のナレッジベース（`search_kb`）が、質問内容に応じて適切に使い分けられている

## 手順

### 手順1: `MCPClient`に必要なクラスをインポートする

`agent.py`の`TODO 1`に、以下を貼り付けます。

```python title="agent.py（TODO 1）"
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient
```

### 手順2: `kb_mcp_server.py`に接続する`MCPClient`を定義する

`TODO 2`に、以下を貼り付けます。

```python title="agent.py（TODO 2）"
kb_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="python", args=["kb_mcp_server.py"])
    )
)
```

`stdio`トランスポートでは、`MCPClient`が`python kb_mcp_server.py`をサブプロセスとして自動的に起動してくれるため、事前に別のターミナルでサーバーを立ち上げておく必要はありません。

### 手順3: `support_agent`をMCP対応に書き換える

`create_support_agent`関数内の`tools`と`system_prompt`を、`TODO 3`として次のように書き換えます。

```python title="agent.py（TODO 3・書き換え）"
new_support_agent = Agent(
    model=model,
    tools=[search_faq, get_ticket_status, get_password_reset_guide, request_account_unlock, kb_client],
    session_manager=session_manager,
    interventions=[hitl],
    system_prompt=(
        "あなたは社内ITヘルプデスクのユーザーサポート担当です。質問内容に応じて適切なツールを使ってください。"
        "社内のFAQ(VPN・パスワード・Wi-Fi等)にはsearch_faqを使い、"
        "経費精算・会議室予約の使い方・名刺発注等、FAQに含まれない社内手続きの質問にはsearch_kbを使ってください。"
        "アカウントロックの解除を求められた場合は、request_account_unlockツールを使ってください。"
    ),
)
```

`kb_client`は、`MCPClient`のインスタンスそのものを`tools=[...]`の中に直接含めるだけで使えます。接続の確立・終了はSDK側が自動的に管理してくれるため、`with`文などで明示的に接続を開始する必要はありません。`system_prompt`には、ローカルFAQとナレッジベースをどう使い分けるかの判断基準を追記しています。

### 手順4: 動作確認する

`TODO 4`（`if __name__ == "__main__":`ブロック）に、以下のコードを貼り付けます。

```python title="agent.py（TODO 4）"
support_agent_1 = create_support_agent("TCK-2001")

result1 = support_agent_1("経費精算のやり方を教えてください。")
print(result1)

result2 = support_agent_1("パスワードを忘れてしまいました。どうすればいいですか?")
print(result2)
```

ターミナルで実行します。

```bash
python agent.py
```

1つ目の問い合わせには、ローカルのFAQには含まれない内容のため、MCP経由の`search_kb`が呼ばれて経費精算に関する回答が返るはずです。2つ目の問い合わせには、これまでと同様にローカルの`search_faq`が呼ばれることを確認してください。ツール呼び出しのたびに`[履歴記録]`の行が出力されるので、どちらのツールが実際に呼ばれたかも確認できます。

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
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient


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


kb_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="python", args=["kb_mcp_server.py"])
    )
)


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
    """チケットIDをセッションIDとする、永続化・Hook・HITL・MCP対応のsupport_agentを生成する。"""
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
        tools=[search_faq, get_ticket_status, get_password_reset_guide, request_account_unlock, kb_client],
        session_manager=session_manager,
        interventions=[hitl],
        system_prompt=(
            "あなたは社内ITヘルプデスクのユーザーサポート担当です。質問内容に応じて適切なツールを使ってください。"
            "社内のFAQ(VPN・パスワード・Wi-Fi等)にはsearch_faqを使い、"
            "経費精算・会議室予約の使い方・名刺発注等、FAQに含まれない社内手続きの質問にはsearch_kbを使ってください。"
            "アカウントロックの解除を求められた場合は、request_account_unlockツールを使ってください。"
        ),
    )
    new_support_agent.add_hook(record_interaction_history, AfterToolCallEvent)
    return new_support_agent


if __name__ == "__main__":
    support_agent_1 = create_support_agent("TCK-2001")

    result1 = support_agent_1("経費精算のやり方を教えてください。")
    print(result1)

    result2 = support_agent_1("パスワードを忘れてしまいました。どうすればいいですか?")
    print(result2)
```

</details>

## チャレンジ演習（任意）

`get_article`ツールを使い、`search_kb`で見つけた記事IDから、記事の全文を取得する2段階の問い合わせをエージェントに行わせてみましょう。

<details>
<summary>チャレンジ演習の模範解答例を表示</summary>

```python
# TODO 4に追記する例
support_agent_2 = create_support_agent("TCK-2002")
result3 = support_agent_2(
    "会議室予約システムの使い方について、記事を検索して、見つかった記事の全文を見せてください。"
)
print(result3)
```

`search_kb`で記事ID（例: `KB-002`）を見つけたうえで、続けて`get_article`を呼び出して全文を取得する、という2段階のツール呼び出しをエージェントが自律的に行う様子を確認できます。

</details>

## 次の演習へ

演習⑥では、ガードレールによる入出力の制御と、エージェントの評価（Evals）を取り上げます。これでコース全体の一貫シナリオが完成します。演習⑥のベースコード（`code/ex6_guardrails_evals/agent.py`）には、この演習の完成形がすでに組み込まれています。
