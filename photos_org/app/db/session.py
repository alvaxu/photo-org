"""
数据库会话管理模块

负责数据库连接和会话管理，包括：
1. 数据库引擎创建
2. 会话管理
3. 连接池配置
4. 事务管理

作者：AI助手
创建日期：2025年9月9日
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    f"sqlite:///{settings.database.path}",
    connect_args={
        "check_same_thread": False,  # SQLite多线程支持
    },
    poolclass=StaticPool,  # 使用静态连接池
    echo=settings.debug,  # 调试模式下显示SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    获取数据库会话

    使用示例：
        db = get_db()
        try:
            # 使用db进行数据库操作
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """获取数据库会话（同步方法）"""
    return SessionLocal()


def create_database():
    """创建数据库和表结构"""
    from app.models import base
    base.Base.metadata.create_all(bind=engine)


def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    from app.models import base
    base.Base.metadata.drop_all(bind=engine)
    base.Base.metadata.create_all(bind=engine)
