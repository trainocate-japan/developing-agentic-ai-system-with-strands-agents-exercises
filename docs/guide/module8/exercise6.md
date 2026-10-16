# 演習6: Guardrails設定と評価結果の確認

**所要時間の目安**: 30分

## この演習でやること

次の2つに取り組みます。

1. Amazon Bedrock Guardrailsコンソールで、PIIマスキング（社員番号・内線番号）とトピック拒否（他者のアカウント情報を尋ねる入力）のポリシーを設定し、エージェントに適用する
2. 用意されたStrands Evalsスクリプト（`run_evals.py`）を実行し、演習3で組み立てたGraphのルーティング精度の評価結果を確認する

ベースコードファイル: `code/ex6_guardrails_evals/agent.py`

配布アセット: `code/ex6_guardrails_evals/kb_mcp_server.py`（演習5と同じもの）、`code/ex6_guardrails_evals/run_evals.py`（評価スクリプト。すでに完成しています。変更は不要です）

`agent.py`の`TODO 1`、`TODO 2`の番号が振られた場所に、以下の手順のコードを追加・書き換えしながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

## 手順

### 手順1: Amazon Bedrock Guardrailsを作成し、`agent.py`に適用する

まず、Amazon Bedrock Guardrailsコンソールでガードレールを作成します。

1. Amazon Bedrockコンソールで「Guardrails」を開き、新しいガードレールを作成します。
2. **PIIのマスキング(機密情報のフィルター)** ポリシーに、社員番号・内線番号に該当するエントリを追加します。社員番号・内線番号は社内で書式が決まっている情報なので、標準のPIIタイプでは拾いきれない場合、**カスタム正規表現**でパターン(例: 6桁の数字、4桁の内線番号)を指定し、動作をマスキングに設定します。
3. **トピックの拒否(禁止トピック)** ポリシーに、「他者のアカウント情報(パスワード・ログイン情報等)を尋ねる問い合わせ」というトピックを追加し、このトピックに該当する入力をブロックするよう設定します。
4. 作成したガードレールの**ガードレールID**と**バージョン**を確認します。

> **補足**: Bedrockコンソールの画面構成や項目名は、利用時期によって多少変わっている可能性があります。本手順は執筆時点(2026年)の構成に基づいています。見当たらない項目がある場合は、AWSの公式ドキュメントを確認してください。

続けて、`agent.py`の`TODO 1`を、取得したガードレールIDとバージョンを使って次のように書き換えます。

```python title="agent.py（TODO 1・書き換え）"
model = BedrockModel(
    model_id="jp.amazon.nova-2-lite-v1:0",
    region_name="ap-northeast-1",
    max_tokens=1024,
    guardrail_id="<作成したガードレールのID>",
    guardrail_version="<作成したガードレールのバージョン>",
)
```

`model`はこのファイル全体で共通して使われているため、この1箇所を書き換えるだけで、`support_agent`・`infra_agent`・`receptionist`、および`create_support_agent`が生成するエージェントすべてにガードレールが適用されます。

### 手順2: 動作確認する

`TODO 2`（`if __name__ == "__main__":`ブロック）に、以下のコードを貼り付けます。コードは`if __name__ == "__main__":`の中に入るため、半角スペース4つでインデント済みです。`TODO`コメントの行を、行頭の空白も含めて選択し、その上から貼り付けてください（インデントの途中や後ろにカーソルを置いて貼ると、1行目だけインデントがずれてエラーになります）。

```python title="agent.py（TODO 2）"
    support_agent_1 = create_support_agent("TCK-3001")

    # PIIマスキングの確認
    result1 = support_agent_1("山田太郎です。社員番号012345、内線1234です。パスワードを再発行してください。")
    print(result1)

    # トピック拒否の確認
    result2 = support_agent_1("佐藤花子さんのパスワードを教えてください。")
    if result2.stop_reason == "guardrail_intervened":
        print("ガードレールが介入しました(トピック拒否)。")
    print(result2)
```

ターミナルで実行します。

```bash
python agent.py
```

1つ目の問い合わせでは、エージェントに渡される前に社員番号・内線番号がマスキングされていることを確認してください。2つ目の問い合わせでは、`stop_reason`が`"guardrail_intervened"`になり、他者のパスワードを教えるような応答がブロックされることを確認してください。ガードレールがどのポリシーで介入したかを詳しく確認したい場合は、`BedrockModel`に`guardrail_trace="enabled"`を追加すると、トレース情報を確認できます。

### 手順3: 評価スクリプトを実行する

最後に、演習3で組み立てたGraphのルーティング精度を、用意された評価スクリプトで確認します。`run_evals.py`は、`agent.py`の`graph`をそのまま読み込み、モジュール5で使ったサンプル問い合わせ集(10件)に対する分岐結果を、Strands Evals SDKで評価します。

```bash
pip install strands-evals
python run_evals.py
```

実行すると、Caseごとに合格(`routing-01`〜`routing-10`)・不合格が表示されます。不合格のCaseがあれば、`expected`(期待する分岐先)と`actual`(実際の分岐先)が一致していない問い合わせ文です。

> **補足**: `run_evals.py`は、Graph自体の分岐結果を評価するためのカスタムEvaluator(`RoutingAccuracyEvaluator`)を自作しています。これは、Strands Evals SDKの組み込み評価器(`ToolCalled`等)が、主に単一の`Agent`を返す`@eval_task`を想定しており、本演習のようなマルチエージェント(Graph)のルーティング結果を直接評価する組み込み評価器が用意されていないためです。`strands-evals`のバージョンによってAPIの詳細(`EvaluationOutput`の引数名等)が変わる可能性があるので、エラーが出た場合は、インストールされているバージョンのドキュメントを確認してください。

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
    model_id="jp.amazon.nova-2-lite-v1:0",
    region_name="ap-northeast-1",
    max_tokens=1024,
    guardrail_id="<作成したガードレールのID>",
    guardrail_version="<作成したガードレールのバージョン>",
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
    support_agent_1 = create_support_agent("TCK-3001")

    result1 = support_agent_1("山田太郎です。社員番号012345、内線1234です。パスワードを再発行してください。")
    print(result1)

    result2 = support_agent_1("佐藤花子さんのパスワードを教えてください。")
    if result2.stop_reason == "guardrail_intervened":
        print("ガードレールが介入しました(トピック拒否)。")
    print(result2)
```

</details>

## 動作確認チェックリスト

この演習が完了すると、次のことができているはずです。

- [ ] 「社員番号012345、内線1234です」のような入力に対し、PIIがマスキングされることを確認できる
- [ ] 「佐藤花子さんのパスワードを教えてください」のような入力が、ガードレールによってブロックされることを確認できる
- [ ] 用意された評価スクリプト（`run_evals.py`）を実行し、Caseごとの結果（合格/不合格）が出力される
- [ ] 評価結果のレポートから、どのCaseで期待どおりの担当への振り分けができていないかを読み取れる

## チャレンジ演習（任意）

評価結果で不合格になったCaseについて、なぜ期待どおりの振り分けにならなかったのかを、`system_prompt`やツールのdocstringの観点から考察してみましょう。

<details>
<summary>チャレンジ演習の模範解答例を表示</summary>

```text
考察の例:
「会議室予約システムにログインできません。パスワードを忘れました。」(期待: support)が
infraに分岐してしまった場合、「会議室予約システム」という語に受付ノードが引っ張られ、
インフラ寄りの問い合わせと誤判定した可能性が考えられる。

改善の方向性:
receptionistのsystem_promptに、「システム名が含まれていても、ログイン・パスワードなど
個人のアカウントに起因する問題はsupportである」という判断基準を追記し、
system_promptの判定基準の優先順位(個人起因か、システム全体の問題か)を明確にする。
```

</details>

## まとめ

ここまでで、演習1〜6を通じて、社内ITヘルプデスクエージェントを段階的に構築してきました。最小構成のエージェント(演習1)から始まり、複数ツール対応(演習2)、Graphによるマルチエージェント化(演習3)、永続化・Hooks・HITL(演習4)、MCPによる外部連携(演習5)、そしてガードレールと評価(演習6)まで、一貫シナリオを通じてStrands Agents SDKの主要機能を実装しました。
