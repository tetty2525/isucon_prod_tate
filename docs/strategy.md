# ISUCON チューニング戦略 (strategy.md)

**【現在のインスタンス状況（2026/06/23 確認）】**
- **OS**: Ubuntu 24.04.4 LTS
- **リソース**: メモリ約3.8GB（空き2.7GB） / ディスク15GB（空き4.6GB） / Swap 0GB
- **稼働状況**: `nginx`, `mysql`, `memcached`, `isu-ruby` が現在アクティブ。

**【練り直した戦略方針】**
ディスクの空き容量が4.6GBあるため、1GBのSwapファイル作成は安全に行えます。
メモリは十分空きがあるため、MySQLの `innodb_buffer_pool_size` は後ほど2GB程度まで引き上げる作戦が非常に有効です。

## 1. 初期観測・環境の安定化
- `unattended-upgrades` 無効化
- メモリ4GB（c6i.large）を活かしたMySQL `innodb_buffer_pool_size` 拡張とSwap（1GB）設定
- MySQLスロークエリログ有効化

## 2. 評価・計測基盤の構築とイテレーション
- 計測ツールの導入: `netdata`, `alp`, `pt-query-digest`
- NginxログのLTSV化
- `Makefile` によるログリセット・計測の自動化

## 3. Nginx / アプリ側のチューニング
- Python実装 (`isu-python`) への切り替え
- Nginxからの静的ファイル直接配信 (`try_files`)
- N+1問題の解消 (IN句やWindow関数での一括取得)
- DB側でのLIMIT/JOINによるデータ転送量削減と複合インデックスの追加
