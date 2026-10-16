# 共通準備: モデルIDの書き換え

各演習のベースコード（`agent.py`）の`BedrockModel`には、使用するモデルのIDの代わりに`<使用するモデルのID>`というプレースホルダーが入っています。**各演習の最初に、このプレースホルダーを下記のモデルIDに書き換えてください。** 書き換えないまま実行すると、モデルの指定が正しくない旨のエラーになります。

## 使用するモデルID

本コースの演習では、コスト効率の観点からAmazon Nova 2 Liteを使用します。

```text
jp.amazon.nova-2-lite-v1:0
```

## 書き換え手順

1. 演習のベースコード（`code/`配下の`agent.py`）をcode-serverのエディタで開きます。
2. `Ctrl+F`（Macは`Cmd+F`）で検索ボックスを開き、`使用するモデルのID`を検索します。
3. `model_id=`に書かれている`"<使用するモデルのID>"`の、**`<`と`>`も含めて**、上記のモデルIDに置き換えます。前後のダブルクォート（`"`）は残します。
4. ファイルを保存します（`Ctrl+S`、Macは`Cmd+S`）。

```python title="agent.py（書き換え前）"
model = BedrockModel(
    model_id="<使用するモデルのID>",
    region_name="ap-northeast-1",
    max_tokens=1024,
)
```

```python title="agent.py（書き換え後）"
model = BedrockModel(
    model_id="jp.amazon.nova-2-lite-v1:0",
    region_name="ap-northeast-1",
    max_tokens=1024,
)
```

`region_name`や`max_tokens`など、他の引数は変更しません。

## 書き換えが必要なファイル

演習ごとに別のファイルを使うため、**演習を始めるたびに**、その演習の`agent.py`を書き換えます。

| 演習 | ファイル |
|---|---|
| 演習1 | `code/ex1_minimal_agent/agent.py` |
| 演習2 | `code/ex2_multi_tool/agent.py` |
| 演習3 | `code/ex3_graph/agent.py` |
| 演習4 | `code/ex4_memory_hitl/agent.py` |
| 演習5 | `code/ex5_mcp/agent.py` |
| 演習6 | `code/ex6_guardrails_evals/agent.py` |

> **ガイドや模範解答のコードを貼り付けたとき。** ガイド中のコード例（模範解答を含む）の`model_id`も、`<使用するモデルのID>`になっています。`model = BedrockModel(...)`の部分を貼り付けたときは、同じ手順でモデルIDに書き換えてください。

## うまく動かないとき

- モデルIDの前後に余分な空白がないか、`:0`まで含めて入力できているかを確認してください。
- `<`や`>`が残っていないか、ダブルクォートが欠けていないかを確認してください。
- 上記を確認してもエラーが解消しない場合は、エラーメッセージを控えて講師に声をかけてください。
