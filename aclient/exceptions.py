"""MinerU 异常定义"""


class MinerUException(Exception):
    """基础异常"""
    pass


class AuthenticationError(MinerUException):
    """认证错误"""
    pass


class TaskNotFoundError(MinerUException):
    """任务不存在"""
    pass


class ParseError(MinerUException):
    """解析错误"""
    pass


class TimeoutError(MinerUException):
    """超时错误"""
    pass


class RateLimitError(MinerUException):
    """频率限制"""
    pass


class ApiResponseError(MinerUException):
    """API响应异常"""

    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg
