-- uploads 테이블 생성 SQL 문
use flask-simple-board;

CREATE TABLE `uploads` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `file_path` VARCHAR(150) NOT NULL,
    `file_name` VARCHAR(100) NOT NULL,
    `file_size` INT NOT NULL,
    `post_id` INT NOT NULL,
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE
);