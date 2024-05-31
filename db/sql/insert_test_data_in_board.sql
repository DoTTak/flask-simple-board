-- board 테이블 테스트 데이터 추가 SQL 문
use flask-simple-board;

INSERT INTO `posts` (`title`, `content`, `author`, `created_at`, `updated_at`) VALUES ('첫 번째 게시글', '이것은 첫 번째 게시글입니다.', '작성자1', '2024-05-29 11:34:27', '2024-05-30 14:08:56');
INSERT INTO `posts` (`title`, `content`, `author`, `created_at`, `updated_at`) VALUES ('두 번째 게시글', '이것은 두 번째 게시글입니다.', '작성자2', '2024-05-30 14:08:56', '2024-06-01 09:15:47');
INSERT INTO `posts` (`title`, `content`, `author`, `created_at`) VALUES ('세 번째 게시글', '이것은 세 번째 게시글입니다.', '작성자3', '2024-05-31 16:45:32');
INSERT INTO `posts` (`title`, `content`, `author`, `created_at`) VALUES ('네 번째 게시글', '이것은 네 번째 게시글입니다.', '작성자4', '2024-06-01 09:15:47');
INSERT INTO `posts` (`title`, `content`, `author`, `created_at`) VALUES ('다섯 번째 게시글', '이것은 다섯 번째 게시글입니다.', '작성자5', '2024-06-02 13:22:51');
