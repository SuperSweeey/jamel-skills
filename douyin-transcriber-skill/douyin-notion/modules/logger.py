"""
日志工具模块
"""


class Logger:
    @staticmethod
    def info(msg: str, task_id: str = ""):
        prefix = f"[{task_id}] " if task_id else ""
        print(f"{prefix}[INFO] {msg}")

    @staticmethod
    def success(msg: str, task_id: str = ""):
        prefix = f"[{task_id}] " if task_id else ""
        print(f"{prefix}[OK] {msg}")

    @staticmethod
    def error(msg: str, task_id: str = ""):
        prefix = f"[{task_id}] " if task_id else ""
        print(f"{prefix}[ERROR] {msg}")

    @staticmethod
    def warning(msg: str, task_id: str = ""):
        prefix = f"[{task_id}] " if task_id else ""
        print(f"{prefix}[WARN] {msg}")

    @staticmethod
    def step(step_num: int, total: int, msg: str, task_id: str = ""):
        prefix = f"[{task_id}] " if task_id else ""
        print(f"{prefix}Step {step_num}/{total}: {msg}")
