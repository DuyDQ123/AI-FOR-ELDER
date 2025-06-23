from flask import Flask
from models import db, User, SystemConfig
from config import Config
from werkzeug.security import generate_password_hash
from datetime import datetime
import mysql.connector
import os

def execute_sql_file(filename):
    """Execute SQL commands from a file"""
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="elder_project",
            allow_local_infile=True
        )
        cursor = conn.cursor()
        
        # Enable multiple statement execution
        cursor.execute("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO'")
        cursor.execute("SET foreign_key_checks = 0")
        
        # Read and execute SQL file
        with open(filename, 'r', encoding='utf-8') as file:
            sql_commands = file.read()
            
            # Execute multiple statements
            for command in sql_commands.split(';'):
                if command.strip():
                    cursor.execute(command + ';')
                    
        cursor.execute("SET foreign_key_checks = 1")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Executed SQL file: {filename}")
        
    except Exception as e:
        print(f"Error executing SQL file {filename}: {str(e)}")
        raise

def init_mysql_db():
    """Initialize MySQL database"""
    try:
        # Create and initialize database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS elder_project")
        cursor.close()
        conn.close()
        
        # Execute SQL files in order
        execute_sql_file('database/schema.sql')
        
        # Check if we need to add medicine dispenser fields
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="elder_project"
        )
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM medicines LIKE 'compartment_number'")
        has_dispenser_fields = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        if not has_dispenser_fields:
            execute_sql_file('database/update_db.sql')
            
        # Initialize or update default data
        execute_sql_file('database/init_data.sql')
        
        print("MySQL database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing MySQL database: {str(e)}")
        raise

def init_db():
    try:
        print("Starting database initialization...")
        print("Step 1: Setting up MySQL database structure")
        init_mysql_db()
        
        print("Step 2: Initializing Flask application")
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        print("Database initialization completed successfully!")
        print("\nDefault accounts:")
        print("Super Admin - username: superadmin, password: superadmin123")
        print("Admin - username: admin, password: admin123")
        
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        raise

if __name__ == '__main__':
    init_db()