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

CREATE TABLE `posts` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(100) NOT NULL,
    `content` TEXT NOT NULL,
    `password` VARCHAR(60),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `user_id` INT,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

CREATE TABLE `uploads` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `file_path` VARCHAR(150) NOT NULL,
    `file_name` VARCHAR(100) NOT NULL,
    `file_size` INT NOT NULL,
    `post_id` INT NOT NULL,
    FOREIGN KEY (`post_id`) REFERENCES `posts`(`id`) ON DELETE CASCADE
);