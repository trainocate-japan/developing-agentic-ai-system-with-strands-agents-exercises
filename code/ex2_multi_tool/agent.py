"""
Agentic AI 開発実践 - Strands Agents 版
演習2: 複数ツールを持つ単一エージェント　ベースコード

このファイルには、演習1の完成形があらかじめ組み込まれています。
TODO 1, TODO 2, ... の番号が振られた場所に、演習ガイドの手順に沿って
コードを追加・書き換えてください（番号は追加する順番を表します）。
"""

from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel, Field


model = BedrockModel(
    model_id="jp.amazon.nova-2-lite-v1:0",
    region_name="ap-northeast-1",
    max_tokens=1024,
)


# --- FAQデータ（演習1で追加済み） --------------------------------------------
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


# --- チケットデータ -----------------------------------------------------------
# TODO 1: 手順1で、TICKET_DATAをここに追加


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


# TODO 2: 手順2で、get_ticket_status・get_password_reset_guideツールをここに追加


# --- 構造化出力の型（演習1で追加済み） ----------------------------------------
class SupportAnswer(BaseModel):
    answer: str = Field(description="問い合わせへの回答本文")
    needs_escalation: bool = Field(description="情報システム部へのエスカレーションが必要か")


# --- エージェント -------------------------------------------------------------
# TODO 3: 手順3で、tools と system_prompt を3ツール対応に書き換えます
agent = Agent(
    model=model,
    tools=[search_faq],
    system_prompt="あなたは社内ITヘルプデスクの担当者です。FAQに関する質問にはsearch_faqツールを使って回答してください。",
)


if __name__ == "__main__":
    # TODO 4: 手順4で、3つのツールを試す動作確認コードに書き換えます
    result = agent(
        "パスワードを忘れてしまいました。どうすればいいですか?",
        structured_output_model=SupportAnswer,
    )
    answer = result.structured_output
    print(answer.answer)
    print(answer.needs_escalation)
