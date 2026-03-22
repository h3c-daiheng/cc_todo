import sys
import argparse
import getpass
sys.path.insert(0, ".")  # 确保能导入 backend 模块

from database import SessionLocal, create_tables
from models import User
from services.auth import hash_password

def main():
    parser = argparse.ArgumentParser(description="初始化管理员账号")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    create_tables()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == args.username).first()
        if existing:
            print(f"用户 '{args.username}' 已存在，跳过创建。")
            return
        password = getpass.getpass("请输入管理员密码: ")
        if len(password) < 6:
            print("密码至少需要 6 位")
            sys.exit(1)
        user = User(
            username=args.username, email=args.email,
            password_hash=hash_password(password), is_admin=True
        )
        db.add(user); db.commit()
        print(f"管理员账号 '{args.username}' 创建成功。")
    finally:
        db.close()

if __name__ == "__main__":
    main()
