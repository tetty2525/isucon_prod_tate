-- commentsテーブルのN+1クエリ解消用
ALTER TABLE comments ADD INDEX post_id_created_at_idx (post_id, created_at DESC);
ALTER TABLE comments ADD INDEX user_id_idx (user_id);

-- postsテーブルのタイムライン表示高速化用
ALTER TABLE posts ADD INDEX created_at_idx (created_at DESC);
ALTER TABLE posts ADD INDEX user_id_created_at_idx (user_id, created_at DESC);
