# ==========================================
# DATABASE CONNECTION
# ==========================================

import mysql.connector
from config import Config

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
            port=Config.DB_PORT,
        )
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # 1. CREATE users TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            google_id VARCHAR(255) NULL
        )
    """)
    print("✅ users table checked/created")
    
    # 2. CREATE student_profiles TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            roll_number VARCHAR(50) UNIQUE,
            department VARCHAR(100),
            year INT,
            semester INT,
            cgpa DECIMAL(3,2),
            attendance_percentage DECIMAL(5,2),
            internal_marks DECIMAL(5,2),
            assignments_submitted INT DEFAULT 0,
            total_assignments INT DEFAULT 0,
            disciplinary_notes TEXT,
            extracurricular TEXT,
            profile_image VARCHAR(255) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✅ student_profiles table checked/created")
    
    # 3. CREATE mentor_notes TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mentor_notes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            mentor_id INT NOT NULL,
            note TEXT NOT NULL,
            note_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
            FOREIGN KEY (mentor_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✅ mentor_notes table checked/created")
    
    # 4. CREATE notifications TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            sender_role ENUM('admin', 'mentor') NOT NULL,
            subject VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            sent_to_all BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✅ notifications table checked/created")
    
    # 5. CREATE risk_flags TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_flags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
            risk_factors TEXT,
            attendance_risk BOOLEAN DEFAULT FALSE,
            grade_risk BOOLEAN DEFAULT FALSE,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE
        )
    """)
    print("✅ risk_flags table checked/created")
    
    # 6. CREATE student_notifications TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            notification_id INT NOT NULL,
            student_id INT NOT NULL,
            read_status BOOLEAN DEFAULT FALSE,
            read_at TIMESTAMP NULL,
            FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE
        )
    """)
    print("✅ student_notifications table checked/created")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ All database tables initialized successfully!")
    return True