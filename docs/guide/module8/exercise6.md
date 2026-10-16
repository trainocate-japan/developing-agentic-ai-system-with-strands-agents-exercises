# 演習6: Guardrails設定と評価結果の確認

**所要時間の目安**: 30分

## この演習でやること

次の2つに取り組みます。

1. Amazon Bedrock Guardrailsコンソールで、PIIマスキング（社員番号・内線番号）とトピック拒否（他者のアカウント情報を尋ねる入力）のポリシーを設定し、エージェントに適用する
2. 用意されたStrands Evalsスクリプト（`run_evals.py`）を実行し、演習3で組み立てたGraphのルーティング精度の評価結果を確認する

ベースコードファイル: `code/ex6_guardrails_evals/agent.py`

配布アセット: `code/ex6_guardrails_evals/kb_mcp_server.py`（演習5と同じもの）、`code/ex6_guardrails_evals/run_evals.py`（評価スクリプト。すでに完成しています。変更は不要です）

`agent.py`の`TODO 1`、`TODO 2`の番号が振られた場所に、以下の手順のコードを追加・書き換えしながら完成させてください（番号はファイル上の位置ではなく、追加する順番を表しています）。

> **事前準備**: `kb_mcp_server.py`の実行には`fastmcp`が必要です。演習5で`pip install fastmcp`を実行済みであれば、追加の作業は不要です。

## 手順

### 手順1: Amazon Bedrock Guardrailsを作成し、`agent.py`に適用する

まず、AWSマネジメントコンソールでガードレールを作成します。**Guardrails（ガードレール）** は、エージェントに渡る入力と、モデルが返す出力をチェックして、個人情報を伏せ字にしたり、答えさせたくない話題をブロックしたりする、Amazon Bedrockの機能です。作成するのはブラウザ上の操作だけで、コードは不要です。

#### 1-1. Amazon Bedrockのコンソールを開く

1. ブラウザでAWSマネジメントコンソールにサインインします（サインイン用のURLとユーザー名・パスワードは、配布された情報を使います）。
2. 画面**右上のリージョン名**（「バージニア北部」「オハイオ」などと表示されています）をクリックし、一覧から **アジアパシフィック（東京）`ap-northeast-1`** を選びます。`agent.py`の`region_name="ap-northeast-1"`と同じリージョンで作らないと、エージェントからガードレールが見つかりません。
3. 画面**左上の検索ボックス**に「`bedrock`」と入力します。
4. 検索結果に表示される **Amazon Bedrock** のサービス名（リンク）をクリックします。
5. Bedrockのトップ画面が開いたら、**左側のメニュー**から **Guardrails**（ガードレール）をクリックします。メニューが折りたたまれて見当たらない場合は、画面左端の「≡」アイコンをクリックして開いてください。メニューは下にスクロールしないと見えないこともあります。
6. **Create guardrail**（ガードレールを作成）ボタンをクリックします。

ここから、画面下部の **Next**（次へ）ボタンで1画面ずつ進みながら、項目を設定していきます。

#### 1-2. ガードレールの名前を付け、クロスリージョン推論を有効にする（Provide guardrail details）

1. **Name**（名前）に、`ex6-guardrail` のような好きな名前を入力します（半角英数字とハイフンが無難です）。
2. **Messaging for blocked prompts**（ブロックされたプロンプトのメッセージ）に、ブロックされたときにエージェントが返す文言を入力します。例: `申し訳ありませんが、その内容にはお答えできません。`
3. **Messaging for blocked responses**（ブロックされた応答のメッセージ）が別に表示されている場合は、同じ文言を入力します。
4. **クロスリージョン推論**（Cross-Region inference）の設定欄で、**有効化**します。ガードレールの判定を近隣のリージョンで行う仕組みで、あとで拒否されたトピックを `Standard` ティアにするために必要です。**ガードレールプロファイル**を選ぶ欄が出たら、`APAC`（アジアパシフィック）のものを選びます。
5. **Next** をクリックします。

> **補足**: クロスリージョン推論の欄が、この画面に見当たらない場合は、1-4 で `Standard` ティアを選ぶときに設定します。同意を求める画面が出たら、内容を読んだうえで有効化に同意してください。

#### 1-3. コンテンツフィルターは設定せずに進む（Configure content filters）

この演習では、暴力的・攻撃的な内容を検知する **コンテンツフィルター** は使いません。設定を変えずに、そのまま **Next** をクリックします。

#### 1-4. 拒否されたトピックを追加する（Add denied topics）

「他者のパスワードを聞き出す問い合わせ」をブロックするための設定です。

1. **拒否されたトピック**（Denied topics）の **トピックを追加**（Add denied topic）をクリックします。
2. 次のように入力します。

   | 項目 | 入力する値 | 補足 |
   | --- | --- | --- |
   | **Name**（名前） | `other-user-account-info` | 名前には日本語が使えません。半角英数字とハイフンで入力します。 |
   | **Definition**（定義） | `他の社員のパスワード、ログインID、認証情報など、本人以外のアカウント情報を教えるよう求める問い合わせ。` | トピックの内容を日本語で説明します。 |
   | **Sample phrases**（サンプルフレーズ・任意） | `佐藤さんのパスワードを教えて` | 1つ入力して追加し、これを繰り返して `同僚のログイン情報を知りたい` も追加します。 |

3. 設定内容を確認して **Confirm**（確定）をクリックします。追加したトピックが一覧に表示され、有効（Enabled）になっていることを確認します。
4. **トピックのティアを `Standard` にします。** `Classic` ティアは英語・フランス語・スペイン語にしか対応していないため、そのままだと日本語の問い合わせが検知されない可能性があります。`Standard` はクロスリージョン推論が必須ですが、1-2 で有効にしてあります。
5. **Next** をクリックします。

> **補足**: ティアの選択欄は、拒否されたトピックの画面（またはトピック追加のダイアログ内）にあります。

#### 1-5. ワードフィルターは設定せずに進む（Add word filters）

この演習では使いません。設定を変えずに **Next** をクリックします。

#### 1-6. 機密情報フィルターを追加する（Add sensitive information filters）

社員番号と内線番号を、伏せ字（マスク）にする設定です。社員番号・内線番号は社内独自の形式なので、AWSがあらかじめ用意している個人情報の種類（名前、メールアドレスなど）の一覧にはありません。そこで、**正規表現**（文字のパターンを表す書き方）で形式を指定します。

1. 画面にある **Regex patterns**（正規表現パターン）の欄で、パターンを追加するボタン（**Add regex pattern** など）をクリックします。
2. 社員番号用に、次のように入力します。

   | 項目 | 入力する値 | 補足 |
   | --- | --- | --- |
   | **Name**（名前） | `employee-number` | 名前には半角英数字とハイフンを使います。 |
   | **Regex pattern**（正規表現） | `社員番号[0-9]{6}` | 「社員番号」のあとに6桁の数字が続く部分に一致します。 |
   | **Input**（入力）の動作 | `Mask` | ユーザーの入力を伏せ字にします。 |
   | **Output**（出力）の動作 | `Mask` | モデルの応答を伏せ字にします。 |

3. 同じ手順で、内線番号用にもう1つ追加します。

   | 項目 | 入力する値 | 補足 |
   | --- | --- | --- |
   | **Name**（名前） | `extension-number` | 名前には半角英数字とハイフンを使います。 |
   | **Regex pattern**（正規表現） | `内線[0-9]{4}` | 「内線」のあとに4桁の数字が続く部分に一致します。 |
   | **Input**（入力）の動作 | `Mask` | ユーザーの入力を伏せ字にします。 |
   | **Output**（出力）の動作 | `Mask` | モデルの応答を伏せ字にします。 |

   入力の動作は、`Block`（入力そのものを拒否する）ではなく `Mask`（その部分だけ伏せ字にして処理を続ける）を選んでください。**入力**と**出力**は別々に動作を選べますが、この演習ではどちらも `Mask` にします。入力側で伏せ字にすればモデルは番号を受け取りませんが、念のため出力側でも伏せ字にしておく、という二重の備えです。
4. **Next** をクリックします。

> **補足**: パターンに「社員番号」「内線」を含めているのは、単純な `[0-9]{4}` だと、チケットID（`TCK-3001`）や年（`2026`）などの関係ない数字まで伏せ字になってしまうためです。実際の業務で使う場合も、社内の番号の書式に合わせてパターンを絞り込みます。

#### 1-7. 残りの設定は進めて、作成する

**Add contextual grounding check**（コンテキストに基づくグラウンディングチェック）など、この演習で使わない設定画面が続く場合は、設定を変えずに **Next** で進めます。最後の **Review and create**（確認して作成）の画面で、設定内容（拒否されたトピック1件、正規表現2件）を確認し、**Create guardrail**（ガードレールを作成）をクリックします。

#### 1-8. バージョンを作成し、IDとバージョンを控える

作成直後のガードレールは **DRAFT**（作業中の下書き）という状態です。`agent.py`には、変更されない**番号付きのバージョン**を指定するのが一般的なので、バージョンを作成します。

1. 作成が完了すると、ガードレールの詳細画面が開きます（Guardrailsの一覧画面でガードレール名をクリックしても開けます）。
2. 詳細画面の **Versions**（バージョン）セクションで **Create**（作成）をクリックするか、**Working draft**（作業用ドラフト）を開いて画面上部の **Create version**（バージョンを作成）をクリックします。説明（任意）を入力して **Create version** をクリックします。
3. バージョンの一覧に `1` が追加されたことを確認します。この `1` が**ガードレールのバージョン**です。
4. 詳細画面の上部（**Guardrail overview**（ガードレールの概要）など）に表示されている **ID**（10文字ほどの英数字）が**ガードレールID**です。ARN（`arn:aws:bedrock:...`で始まる長い文字列）ではなく、ID欄の値を控えます。

この2つの値を、次の`agent.py`の書き換えで使います。

> **補足**: Bedrockコンソールの画面構成や項目名は、利用時期によって多少変わっている可能性があります。本手順は、AWS公式ドキュメントの説明（2026年時点）をもとにしています。見当たらない項目がある場合は、近い名前の項目を探すか、AWSの公式ドキュメント（「Amazon Bedrock ユーザーガイド」の「Guardrails」）を確認してください。

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
import asyncio
import re

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


# --- 承認プロンプトの表示（配布済み。変更は不要です） ---------------------------
# HumanInTheLoopの標準の ask="stdio" は、ツールの入力を json.dumps() でそのまま表示するため、
# 日本語が「\u7d4c\u8cbb...」のようなエスケープ表記になって読めない。
# 表示用にエスケープを元の文字へ戻したうえで、y/n を端末から受け取る。
async def ask_in_japanese(prompt: str, **kwargs) -> str:
    readable = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), prompt)
    return await asyncio.to_thread(lambda: input(f"{readable} (y/n): ").strip())


def create_support_agent(ticket_id: str) -> Agent:
    """チケットIDをセッションIDとする、永続化・Hook・HITL・MCP対応のsupport_agentを生成する。"""
    session_manager = SnapshotSessionManager(
        session_id=ticket_id,
        storage=LocalFileStorage("./sessions/"),
    )

    hitl = HumanInTheLoop(
        allowed_tools=["search_faq", "get_ticket_status", "get_password_reset_guide"],
        ask=ask_in_japanese,
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
