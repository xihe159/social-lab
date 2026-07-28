"""兼容旧导入路径。

业务代码仍可继续使用：
    from app.services.session_orchestrator import SessionOrchestrator

真正实现已经迁移到 app.services.session.orchestrator。
"""

from app.services.session.orchestrator import SessionOrchestrator

__all__ = ["SessionOrchestrator"]
