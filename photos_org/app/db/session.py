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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.core.config import settings

def optimize_database_connection(db: Session):
    """优化数据库连接设置"""
    try:
        # 🔥 启用WAL模式（提高并发性能）
        db.execute(text("PRAGMA journal_mode=WAL"))
        
        # 🔥 设置同步模式为NORMAL（平衡性能和安全性）
        db.execute(text("PRAGMA synchronous=NORMAL"))
        
        # 🔥 设置缓存大小为64MB
        db.execute(text("PRAGMA cache_size=-64000"))
        
        # 🔥 设置临时存储为内存模式
        db.execute(text("PRAGMA temp_store=MEMORY"))
        
        # 🔥 保持外键约束关闭（按用户要求）
        # db.execute(text("PRAGMA foreign_keys=ON"))
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e

# 创建数据库引擎
engine = create_engine(
    f"sqlite:///{settings.database.path}",
    connect_args={
        "check_same_thread": False,  # SQLite多线程支持
        "timeout": 30,  # 🔥 连接超时30秒
    },
    poolclass=QueuePool,  # 🔥 使用队列连接池
    pool_size=10,         # 🔥 基础连接池大小
    max_overflow=20,      # 🔥 最大溢出连接
    pool_timeout=30,      # 🔥 获取连接超时
    pool_pre_ping=True,   # 🔥 连接前检查
    echo=settings.debug,  # 调试模式下显示SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    获取数据库会话并自动优化

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
        # 🔥 自动优化数据库连接
        optimize_database_connection(db)
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
