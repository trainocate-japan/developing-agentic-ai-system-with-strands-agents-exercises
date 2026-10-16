"""
Agentic AI 開発実践 - Strands Agents 版
演習6: Guardrails設定と評価結果の確認　ベースコード

このファイルには、演習5の完成形があらかじめ組み込まれています。
TODO 1, TODO 2 の番号が振られた場所に、演習ガイドの手順に沿って
コードを追加・書き換えてください（番号は追加する順番を表します）。

このファイルと同じディレクトリに、配布された kb_mcp_server.py を置いてください。
評価(Evals)は、別ファイルの run_evals.py で実行します。
"""

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


# --- モデル -------------------------------------------------------------------
# TODO 1: 手順1で、guardrail_id・guardrail_versionを追加します
model = BedrockModel(
    model_id="jp.amazon.nova-2-lite-v1:0",
    region_name="ap-northeast-1",
    max_tokens=1024,
)


# --- FAQデータ（演習1で追加済み） ----------------------------------------------
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


# --- チケットデータ（演習2で追加済み） ------------------------------------------
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


# --- 稼働状況データ（演習3で追加済み） ------------------------------------------
SYSTEM_STATUS = {
    "VPN": {"status": "正常", "last_checked": "2026-09-20 09:00"},
    "社内ポータル": {"status": "正常", "last_checked": "2026-09-20 09:00"},
    "メールサーバー": {"status": "一部障害", "last_checked": "2026-09-20 08:30"},
    "会議室予約システム": {"status": "正常", "last_checked": "2026-09-20 09:00"},
}


# --- ツール -------------------------------------------------------------------
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


# --- 構造化出力の型（演習1で追加済み） ------------------------------------------
class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")


# --- エージェント（演習3で追加済み） --------------------------------------------
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


# --- 対応履歴の記録(Hook)（演習4で追加済み） -----------------------------------
def record_interaction_history(event: AfterToolCallEvent) -> None:
    """ツール呼び出しの結果を、対応履歴として記録する。"""
    print(f"[履歴記録] ツール: {event.tool_use['name']} / 結果: {event.result}")
    # 実際の運用では、ここでTICKET_DATAへの追記やログ基盤への送信を行う


# --- セッション管理・Hook・HITL・MCP対応のsupport_agent（演習5で追加済み） --------
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
    # TODO 2: 手順2で、ガードレールの動作確認コードをここに追加
    pass
