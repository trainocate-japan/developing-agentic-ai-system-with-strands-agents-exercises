# developing-agentic-ai-system-with-strands-agents-exercises

「Agentic AI 開発実践 - Strands Agents 版」研修コースの、受講者向け演習教材リポジトリです。

講師デモ用コード（`developing-agentic-ai-with-strands-agents`リポジトリ）とは別リポジトリとして管理しています。

## 構成

```
code/                           演習の配布用ベースコード・アセット
  ex1_minimal_agent/
    agent.py                    演習1: 最小構成エージェント
  ex2_multi_tool/
    agent.py                    演習2: 複数ツールを持つ単一エージェント
  ex3_graph/
    agent.py                    演習3: Graphによる一次切り分け
  ex4_memory_hitl/
    agent.py                    演習4: 永続化・Hooks・HITL
  ex5_mcp/
    agent.py                    演習5: MCPサーバーへの接続
    kb_mcp_server.py            配布アセット: 社内ナレッジベースMCPサーバー
  ex6_guardrails_evals/
    agent.py                    演習6: Guardrails設定と評価結果の確認
    kb_mcp_server.py            配布アセット(演習5と同じ)
    run_evals.py                配布アセット: ルーティング精度の評価スクリプト

docs/                            演習ガイド(VuePressサイトのソース)
  guide/
    module3/exercise1.md
    module4/exercise2.md
    module5/exercise3.md
    module6/exercise4.md
    module7/exercise5.md
    module8/exercise6.md
```

各`agent.py`には、`TODO 1`, `TODO 2`, ... と番号が振られた場所があります。番号はファイル上の位置ではなく、`docs/guide/`配下の対応する演習ガイドの手順で追加する順番を表しています。各演習のベースコードには、前の演習の完成形があらかじめ組み込まれています。

## 今後の予定

- VuePressプロジェクトとしての体裁（`.vuepress/config.js`、`package.json`等）はまだ整備していません。現時点では、各演習のMarkdownガイドとベースコードのみが含まれています。
- GitHub Pagesへの公開・GitHub Actionsによる自動デプロイは、別途実装予定です。
