# 第2次チューニングプラン (Wave 2): DBインデックスの追加

## 分析結果の振り返り
先ほどのベンチマークで以下の大きなボトルネックが判明しました。

1. **DBのフルスキャン（重いSQL）**
   `pt-query-digest` の結果から、トップページ表示時に呼ばれる以下のSQLが致命的に遅いことが判明しました。
   `SELECT * FROM comments WHERE post_id = ? ORDER BY created_at DESC LIMIT 3`
   このSQLは1回呼ばれるごとに **約9万7千行（ほぼ全行）** をスキャンしており、ベンチマーク中に合計で**76秒**もDBを占有していました（完全なインデックス不足です）。

2. **画像のDB配信の限界**
   `alp` の結果から、依然として `/image/[0-9]+` が合計で433秒もかかっており、Pythonを通じた画像のDB配信が最大の重りになっています。

## Proposed Changes (修正方針)

まずは効果が最も高く、簡単に修正できる **「DBへのインデックス追加」** を行います。画像のファイル化（Nginx直接配信）はさらに大きなコード変更が必要になるため、次回のWave 3で行う予定です。

以下のインデックスをMySQLに追加します。
```sql
-- commentsテーブルのN+1クエリ解消用
ALTER TABLE comments ADD INDEX post_id_created_at_idx (post_id, created_at DESC);
ALTER TABLE comments ADD INDEX user_id_idx (user_id);

-- postsテーブルのタイムライン表示高速化用
ALTER TABLE posts ADD INDEX created_at_idx (created_at DESC);
ALTER TABLE posts ADD INDEX user_id_created_at_idx (user_id, created_at DESC);
```

### 適用方法
ISUCON（Private-isu）の仕様上、初期化時（`/initialize`）にテーブルのDROP/CREATEが走らないため、直接MySQLに上記の `ALTER TABLE` を流し込むだけで永続化されます。（念のためファイルにも残しておきます）

---
## User Review Required

上記の方針でよろしいでしょうか？
「承認」いただけましたら、サーバー上で直接インデックスを追加するSQLを実行し、再度ベンチマーク（Wave 2）に進みます！
