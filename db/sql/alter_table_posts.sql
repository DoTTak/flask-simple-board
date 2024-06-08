-- 기존 posts 테이블의 구조(create_table_board.sql) 수정
use flask-simple-board;

ALTER TABLE `posts`
DROP 
    COLUMN `author`,
ADD
    COLUMN `user_id` INT,
ADD
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE;