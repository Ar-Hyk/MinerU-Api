"""MinerU-API 配置管理"""
import os
from typing import Optional

# 默认值
DEFAULT_BASE_URL = "https://mineru.net/api/v4"
DEFAULT_TIMEOUT = 300
DEFAULT_POLL_INTERVAL = 2
MAX_RETRIES = 3


class Config:
    """
    配置管理类
    优先级逻辑：传入参数 > 环境变量 > 默认值
    """

    def __init__(
            self,
            api_token: Optional[str] = None,
            base_url: Optional[str] = None,
            timeout: Optional[int] = None,
            poll_interval: Optional[int] = None,
            max_retries: Optional[int] = None
    ):
        """
        初始化加载配置，优先级逻辑：传入参数 > 环境变量 > 默认值
        :param api_token: 必须，从环境变量MINERU_API_TOKEN中读取
        :param base_url: 非必须，从环境变量MINERU_API_BASE_URL中读取
        :param timeout: 非必须，从环境变量MINERU_TIMEOUT中读取
        :param poll_interval: 非必须，从环境变量MINERU_POLL_INTERVAL中读取
        :param max_retries: 非必须，从环境变量MINERU_MAX_RETRIES中读取
        """

        self.api_token = self._get_value(direct=api_token, env_var="MINERU_API_TOKEN", default=None, required=True)

        self.base_url = self._get_value(direct=base_url, env_var="MINERU_API_BASE_URL", default=DEFAULT_BASE_URL)

        self.timeout = int(
            self._get_value(direct=timeout, env_var="MINERU_TIMEOUT", default=DEFAULT_TIMEOUT)
        )

        self.poll_interval = int(
            self._get_value(direct=poll_interval, env_var="MINERU_POLL_INTERVAL", default=DEFAULT_POLL_INTERVAL)
        )

        self.max_retries = int(
            self._get_value(direct=max_retries, env_var="MINERU_MAX_RETRIES", default=MAX_RETRIES)
        )

    @staticmethod
    def _get_value(
            direct: Optional[str],
            env_var: str,
            default: Optional[str | int] = None,
            required: bool = False
    ) -> Optional[str]:
        """
        获取配置值
        :param direct: 传参
        :param env_var: 环境变量名
        :param default: 默认值
        :param required: 是否必须
        """
        # 1. 优先使用传参
        if direct is not None: return direct
        # 2. 其次使用环境变量
        env_value = os.getenv(env_var)
        if env_value is not None: return env_value
        # 3. 使用默认值
        if default is not None: return default
        # 4. 必填检查
        if required: raise ValueError(f"{env_var} 必须配置（传参或环境变量）")
        return None

    def validate(self) -> None:
        """验证配置"""
        if not self.api_token:
            raise ValueError("API token 未配置，请通过参数或环境变量 MINERU_API_TOKEN 设置")
        if isinstance(self.api_token, Config):
            raise ValueError("API token 配置错误! Config对象需要用'config=config' 传递")
        if not self.base_url.startswith("http"):
            raise ValueError(f"base_url 必须是有效的URL: {self.base_url}")
        if self.timeout <= 0:
            raise ValueError("timeout 必须为正整数")
        if self.poll_interval <= 0:
            raise ValueError("poll_interval 必须为正整数")

    def __repr__(self):
        """调试用"""
        return (
            f"Config(api_token={self.api_token!r}, base_url={self.base_url!r}, "
            f"timeout={self.timeout}, poll_interval={self.poll_interval}, max_retries={self.max_retries})"
        )
