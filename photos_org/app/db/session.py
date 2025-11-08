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

# 全局引擎实例（延迟初始化）
_engine_instance = None
_SessionLocal = None


def get_engine():
    """
    获取数据库引擎（延迟初始化）
    
    首次调用时创建引擎，后续调用返回同一个引擎。
    这样可以确保在 setup_msix_first_run() 完成后再初始化数据库引擎。
    """
    global _engine_instance, _SessionLocal
    if _engine_instance is None:
        from app.core.config import get_settings
        settings = get_settings()
        
        _engine_instance = create_engine(
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
            echo=getattr(settings, 'debug', False),  # 调试模式下显示SQL语句
)

# 创建会话工厂
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine_instance)
    
    return _engine_instance


def reload_engine():
    """
    重新创建引擎（用于配置更新后）
    
    在配置更新后调用此函数，会重新创建引擎，使用最新的数据库路径。
    """
    global _engine_instance, _SessionLocal
    if _engine_instance is not None:
        _engine_instance.dispose()
    _engine_instance = None
    _SessionLocal = None
    return get_engine()


def get_session_local():
    """
    获取会话工厂（延迟初始化）
    
    首次调用时创建会话工厂，后续调用返回同一个工厂。
    """
    if _SessionLocal is None:
        get_engine()  # 这会创建引擎和会话工厂
    return _SessionLocal


# 为了向后兼容，提供 engine 和 SessionLocal
# 注意：为了延迟初始化，这里使用包装函数
def _get_engine():
    """向后兼容：获取引擎"""
    return get_engine()

def _get_session_local():
    """向后兼容：获取会话工厂"""
    return get_session_local()

# 创建包装对象
class _EngineWrapper:
    """Engine 包装类，用于延迟初始化"""
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    
    def __call__(self, *args, **kwargs):
        return get_engine()(*args, **kwargs)

class _SessionLocalWrapper:
    """SessionLocal 包装类，用于延迟初始化"""
    def __call__(self, *args, **kwargs):
        return get_session_local()(*args, **kwargs)

# 为了向后兼容，提供 engine 和 SessionLocal 对象
engine = _EngineWrapper()
SessionLocal = _SessionLocalWrapper()


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
    db = get_session_local()()
    try:
        # 🔥 自动优化数据库连接
        optimize_database_connection(db)
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """获取数据库会话（同步方法）"""
    return get_session_local()()


def create_database():
    """创建数据库和表结构"""
    from app.models import base
    base.Base.metadata.create_all(bind=get_engine())


def reset_database():
    """重置数据库（删除所有表并重新创建）"""
    from app.models import base
    base.Base.metadata.drop_all(bind=get_engine())
    base.Base.metadata.create_all(bind=get_engine())
