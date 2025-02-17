members = { "analyzer_by_llm": 'データをLLMを用いて分析します。テキストの要約や、キーワードの抽出などテキストの分析に関するタスクが得意です。出力は全てテキストであり、グラフや図などは生成できません。。',
           "analyzer_by_code": "データベースに保存されたデータ、もしくは提供されたデータを分析するためのコードを生成し、実行できます。データをもとにグラフや図などを生成できます。",
           }

options = members.copy()
options['FINISH'] = "質問の要求を満たす回答を生成することができたと判断し、処理を終了させるときに選択してください。"