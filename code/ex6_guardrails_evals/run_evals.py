"""
Agentic AI 開発実践 - Strands Agents 版
演習6: ルーティング精度の評価スクリプト（配布アセット）

このファイルは配布用の完成済みアセットです。演習でこのファイルの実装を
変更する必要はありません。agent.py・kb_mcp_server.pyと同じディレクトリに置き、
`python run_evals.py` で実行してください。

演習3で組み立てたGraph(receptionist → support / infra)が、
モジュール5のサンプル問い合わせ集(SAMPLE_INQUIRIES)に対して、
期待どおりの担当に振り分けられているかを、Strands Evals SDKで評価します。
"""

from strands_evals import eval_task, Case, Experiment, TracedHandler
from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationOutput

from agent import graph

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


@eval_task(TracedHandler())
def run_routing_task(case: Case) -> dict:
    """1件の問い合わせ(case.input)をGraphに流し、実際に到達した担当を返す。

    Strands Evalsは、タスク関数の戻り値のうち"output"キーの値を、評価器に
    actual_outputとして渡す。
    """
    result = graph(case.input)
    actual_route = "infra" if "infra" in result.results else "support"
    return {"output": {"route": actual_route}}


class RoutingAccuracyEvaluator(Evaluator):
    """Graphの分岐結果(dict)が、期待する分岐先と一致するかを判定する評価器。

    Strands Evalsの組み込み評価器(ToolCalled等)は、@eval_taskがAgentを返す
    ケースを主な対象としており、本演習のようにGraph自体の分岐結果を評価する
    組み込み評価器は用意されていない。そのため、カスタムのEvaluatorを自作している。
    """

    def evaluate(self, evaluation_case) -> list[EvaluationOutput]:
        actual_route = evaluation_case.actual_output.get("route")
        expected_route = evaluation_case.expected_output.get("route")
        passed = actual_route == expected_route
        return [
            EvaluationOutput(
                score=1.0 if passed else 0.0,
                test_pass=passed,
                reason=f"expected={expected_route}, actual={actual_route}",
            )
        ]


cases = [
    Case(
        name=f"routing-{i + 1:02d}",
        input=case["text"],
        expected_output={"route": case["expected_route"]},
    )
    for i, case in enumerate(SAMPLE_INQUIRIES)
]

if __name__ == "__main__":
    experiment = Experiment(cases=cases, evaluators=[RoutingAccuracyEvaluator()])
    report = experiment.run_evaluations(run_routing_task)

    # Caseごとの結果(合格/不合格、期待する分岐先と実際の分岐先)を表示する
    for case, passed, reason in zip(report.cases, report.test_passes, report.reasons):
        print(f"{case['name']}: {'合格' if passed else '不合格'} ({reason}) {case['input']}")
    print(f"合格 {sum(report.test_passes)}/{len(report.test_passes)} 件 (正答率 {report.overall_score:.0%})")
