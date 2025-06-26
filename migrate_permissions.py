#!/usr/bin/env python3
"""
数据库迁移脚本：添加用户权限字段
"""

import sqlite3
import os
from pathlib import Path

def migrate_permissions():
    """迁移用户表，添加权限字段"""
    db_path = Path("instance/users.db")
    
    if not db_path.exists():
        print("数据库文件不存在，跳过迁移")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加缺失的字段
        if 'can_download' not in columns:
            print("添加 can_download 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN can_download BOOLEAN DEFAULT 1")
        
        if 'can_delete' not in columns:
            print("添加 can_delete 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN can_delete BOOLEAN DEFAULT 0")
        
        # 提交更改
        conn.commit()
        print("权限字段迁移完成")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"当前用户表字段: {columns}")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_permissions() 