-- users 테이블 생성 SQL 문
use flask-simple-board;

CREATE TABLE `users` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `email` VARCHAR(50) UNIQUE KEY,
    `name` VARCHAR(50) NOT NULL,
    `password` VARCHAR(60) NOT NULL,
    `school` VARCHAR(50) NOT NULL,
    `introduce` TEXT ,
    `profile_name` VARCHAR(100),
    `profile_path` VARCHAR(150),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);