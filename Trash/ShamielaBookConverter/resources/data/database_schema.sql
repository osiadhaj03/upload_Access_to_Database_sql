-- هيكل قاعدة البيانات لمحول كتب الشاملة
-- Database schema for Shamela Books Converter

-- جدول المؤلفين
CREATE TABLE IF NOT EXISTS authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    birth_year INT NULL,
    death_year INT NULL,
    biography TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_author_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول الناشرين
CREATE TABLE IF NOT EXISTS publishers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NULL,
    website VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_publisher_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول الكتب
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    author_id INT NOT NULL,
    publisher_id INT NULL,
    publication_year INT NULL,
    description TEXT NULL,
    total_pages INT DEFAULT 0,
    total_volumes INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publishers(id) ON DELETE SET NULL,
    INDEX idx_book_name (name),
    INDEX idx_author_id (author_id),
    INDEX idx_publication_year (publication_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول الصفحات (محسن للنظام الجديد)
CREATE TABLE IF NOT EXISTS pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    internal_index INT AUTO_INCREMENT UNIQUE,
    book_id INT NOT NULL,
    page_number INT NOT NULL,
    volume_number INT DEFAULT 1,
    content LONGTEXT NOT NULL,
    html_content LONGTEXT NULL,
    word_count INT DEFAULT 0,
    character_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    INDEX idx_book_page (book_id, page_number),
    INDEX idx_internal_index (internal_index),
    INDEX idx_volume (book_id, volume_number),
    FULLTEXT KEY ft_content (content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول الفصول (محسن للنظام الجديد)
CREATE TABLE IF NOT EXISTS chapters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    level INT DEFAULT 1,
    parent_id INT NULL,
    start_page_number INT NULL,
    end_page_number INT NULL,
    start_page_internal_index INT NULL,
    end_page_internal_index INT NULL,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES chapters(id) ON DELETE CASCADE,
    FOREIGN KEY (start_page_internal_index) REFERENCES pages(internal_index) ON DELETE SET NULL,
    FOREIGN KEY (end_page_internal_index) REFERENCES pages(internal_index) ON DELETE SET NULL,
    INDEX idx_book_chapter (book_id, level),
    INDEX idx_chapter_title (title),
    INDEX idx_page_range (start_page_internal_index, end_page_internal_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول الفهارس
CREATE TABLE IF NOT EXISTS book_indexes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    term VARCHAR(255) NOT NULL,
    page_references TEXT NULL,
    internal_index_references TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    INDEX idx_book_term (book_id, term),
    FULLTEXT KEY ft_term (term)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول سجلات التحويل
CREATE TABLE IF NOT EXISTS conversion_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NULL,
    source_file VARCHAR(500) NOT NULL,
    conversion_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    pages_converted INT DEFAULT 0,
    chapters_converted INT DEFAULT 0,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL,
    INDEX idx_conversion_status (conversion_status),
    INDEX idx_conversion_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- إجراءات مخزونة مفيدة

-- إجراء للحصول على إحصائيات كتاب
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS GetBookStats(IN book_id_param INT)
BEGIN
    SELECT 
        b.name AS book_name,
        a.name AS author_name,
        p.name AS publisher_name,
        COUNT(DISTINCT pg.id) AS total_pages,
        COUNT(DISTINCT c.id) AS total_chapters,
        AVG(pg.word_count) AS avg_words_per_page,
        SUM(pg.word_count) AS total_words,
        b.created_at AS conversion_date
    FROM books b
    LEFT JOIN authors a ON b.author_id = a.id
    LEFT JOIN publishers p ON b.publisher_id = p.id
    LEFT JOIN pages pg ON b.id = pg.book_id
    LEFT JOIN chapters c ON b.id = c.book_id
    WHERE b.id = book_id_param
    GROUP BY b.id;
END //
DELIMITER ;

-- إجراء للبحث في النصوص
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS SearchInBooks(IN search_term VARCHAR(255))
BEGIN
    SELECT 
        b.name AS book_name,
        a.name AS author_name,
        pg.page_number,
        pg.volume_number,
        SUBSTRING(pg.content, 1, 200) AS excerpt,
        MATCH(pg.content) AGAINST(search_term IN NATURAL LANGUAGE MODE) AS relevance_score
    FROM pages pg
    JOIN books b ON pg.book_id = b.id
    JOIN authors a ON b.author_id = a.id
    WHERE MATCH(pg.content) AGAINST(search_term IN NATURAL LANGUAGE MODE)
    ORDER BY relevance_score DESC
    LIMIT 100;
END //
DELIMITER ;

-- عرض لإحصائيات المجموعة
CREATE VIEW IF NOT EXISTS collection_stats AS
SELECT 
    COUNT(DISTINCT b.id) AS total_books,
    COUNT(DISTINCT a.id) AS total_authors,
    COUNT(DISTINCT p.id) AS total_publishers,
    COUNT(DISTINCT pg.id) AS total_pages,
    COUNT(DISTINCT c.id) AS total_chapters,
    SUM(pg.word_count) AS total_words,
    AVG(pg.word_count) AS avg_words_per_page
FROM books b
LEFT JOIN authors a ON b.author_id = a.id
LEFT JOIN publishers p ON b.publisher_id = p.id
LEFT JOIN pages pg ON b.id = pg.book_id
LEFT JOIN chapters c ON b.id = c.book_id;