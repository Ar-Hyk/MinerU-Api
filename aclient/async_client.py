"""MinerU 纯异步客户端"""
import asyncio
from pathlib import Path
from typing import Union, AsyncGenerator

import aiohttp
from aiohttp import ClientTimeout

from .config import Config
from .models import *


class AsyncMinerUClient:
    """MinerU 异步客户端"""

    def __init__(self,
                 api_token: Optional[str] = None,
                 base_url: Optional[str] = None,
                 timeout: Optional[int] = None,
                 poll_interval: Optional[int] = None,
                 max_retries: int = None,
                 config: Optional[Config] = None):
        """
        初始化客户端
        1. 用传参（api_token, base_url等）
        2. 用Config实例
        3. 用环境变量（自动读取）
        """
        # 1、用传参创建Config
        if any([api_token, base_url, timeout, poll_interval]):
            self.config = Config(
                api_token=api_token,
                base_url=base_url,
                timeout=timeout,
                poll_interval=poll_interval,
                max_retries=max_retries
            )
        # 2、用Config实例
        elif config:
            if not isinstance(config, Config):
                raise TypeError("config 必须是 Config 类型的实例")
            self.config = config
        # 3、自动创建Config（从环境变量读取）
        else:
            self.config = Config()

        # 验证配置
        self.config.validate()

        # 初始化客户端属性
        self._session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=self.config.timeout)

    def __repr__(self) -> str:
        return ("AsyncMinerUClient("
                f"api_token={self.config.api_token!r}, "
                f"base_url={self.config.base_url!r}, "
                f"timeout={self.config.timeout}, "
                f"poll_interval={self.config.poll_interval}, "
                f"max_retrie={self.config.max_retries})")

    async def __aenter__(self):
        """上下文管理器入口"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        await self.close()

    async def _ensure_session(self):
        """确保session已创建"""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        """关闭session"""
        if self._session and not self._session.closed: await self._session.close()

    def _headers(self, use_content_type: bool = True) -> Dict[str, str]:
        """请求头"""
        headers = {"Authorization": f"Bearer {self.config.api_token}"}
        if use_content_type: headers["Content-Type"] = "application/json"
        return headers

    async def _send_request(self, method: str, endpoint: str, **kwargs) -> 'Response':
        """发送请求并处理错误"""
        url = f"{self.config.base_url}/{endpoint}"
        headers = self._headers(kwargs.get('use_content_type', True))

        for attempt in range(self.config.max_retries + 1):
            try:
                await self._ensure_session()
                async with self._session.request(method=method, url=url, headers=headers, **kwargs) as response:
                    response.raise_for_status()
                    api_response = Response.from_dict(await response.json())
                    api_response.raise_for_status()
                    return api_response

            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    raise AuthenticationError("API Token 无效或已过期")
                elif e.status == 404:
                    raise TaskNotFoundError("资源不存在")
                elif e.status == 422:
                    error_text = await e.response.text()
                    raise ParseError(f"参数错误: {error_text}")
                # 5xx错误自动重试
                elif e.status >= 500 and attempt < self.config.max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"服务器错误 {e.status}，第 {attempt + 1}/{self.config.max_retries} 次重试，"
                          f"等待 {wait_time} 秒...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise MinerUException(f"HTTP {e.status}: {e.message}")

            except asyncio.TimeoutError:
                if attempt < self.config.max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"请求超时，第 {attempt + 1}/{self.config.max_retries}  次重试，"
                          f"等待 {wait_time} 秒...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise TimeoutError(f"请求超时（{self.timeout.total}秒）")

            except ApiResponseError as e:
                if attempt < self.config.max_retries:
                    print(f"API 响应异常 {e.code}: {e.msg}，第 {attempt + 1}/{self.config.max_retries}  次重试...")
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"等待 {wait_time} 秒...")
                    await asyncio.sleep(wait_time)
                    continue
                raise ApiResponseError(e.code, e.msg)

            except Exception as e:
                raise MinerUException(f"请求失败: {str(e)}")

    # ========== 核心接口 ==========

    async def create_task_from_url(self, url: str = None, req: RequestUrlFile = None) -> TaskInfo:
        """从URL创建单个文件解析任务"""
        if url is not None: req = RequestUrlFile(url=url)
        if req is None: raise ValueError('请传入url或RequestUrlFile')
        result = await self._send_request("POST", "extract/task", json=req.dict)
        return result

    async def get_task(self, task_id: str) -> TaskInfo:
        """获取任务详情"""
        result = await self._send_request("GET", f"extract/task/{task_id}")
        return TaskInfo.from_dict(result.data)

    async def create_batch_upload_urls(self, files: list[FileInfo] = None, req: RequestUploadFiles = None):
        """申请文件上传链接"""
        if files is not None: req = RequestUploadFiles(files=files)
        if req is None: raise ValueError('请传入List[FileInfo]或RequestUploadFiles')
        result = await self._send_request("POST", "file-urls/batch", json=req.dict)
        return result

    async def create_batch_tasks(
            self,
            urls: Optional[List[str]] = None,
            file_paths: Optional[List[str]] = None,
            **kwargs
    ) -> BatchTask:
        """批量创建任务"""
        # 注意：此接口需要MinerU支持批量创建
        data = {"tasks": []}

        if urls:
            for url in urls:
                task_data = {"url": url, **kwargs}
                data["tasks"].append(task_data)

        if file_paths:
            raise NotImplementedError("批量文件上传请单独调用 create_task_from_file")

        result = await self._send_request("POST", "extract/batch", json=data)
        data = result["data"]
        return BatchTask(
            batch_id=data["batch_id"],
            task_ids=data["task_ids"],
            status=TaskStatus(data["status"]),
            total=data["total"],
            completed=data["completed"],
            failed=data["failed"]
        )

    async def get_batch_status(self, batch_id: str) -> BatchTask:
        """获取批量任务状态"""
        result = await self._send_request("GET", f"extract/batch/{batch_id}")
        data = result["data"]
        return BatchTask(
            batch_id=batch_id,
            task_ids=data["task_ids"],
            status=TaskStatus(data["status"]),
            total=data["total"],
            completed=data["completed"],
            failed=data["failed"]
        )

    # ========== 高级接口 ==========

    async def wait_for_task(
            self,
            task_id: str,
            poll_interval: int = 2,
            timeout: int = 300
    ) -> TaskInfo:
        """等待任务完成"""
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"等待任务超时（{timeout}秒）")

            task = await self.get_task(task_id)

            if task.is_completed or task.is_failed:
                return task

            await asyncio.sleep(poll_interval)

    async def parse(
            self,
            source: Union[str, Path, bytes],
            file_name: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """一键解析（自动判断来源并等待结果）"""
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            task = await self.create_task_from_url(source, **kwargs)
        elif isinstance(source, (str, Path)):
            task = await self.create_task_from_file(file_path=str(source), **kwargs)
        elif isinstance(source, bytes):
            if not file_name:
                raise ValueError("提供字节数据时必须指定 file_name")
            task = await self.create_task_from_file(file_data=source, file_name=file_name, **kwargs)
        else:
            raise ValueError("source 必须是 URL、文件路径或字节数据")

        completed_task = await self.wait_for_task(task.task_id, **kwargs)

        if completed_task.is_failed:
            raise ParseError(f"解析失败: {completed_task.error}")

        return completed_task.result

    # ========== 工具接口 ==========

    async def get_usage_stats(self) -> UsageStats:
        """获取使用统计"""
        result = await self._send_request("GET", "user/stats")
        data = result["data"]
        return UsageStats(
            total_calls=data["total_calls"],
            success_calls=data["success_calls"],
            failed_calls=data["failed_calls"],
            total_cost_time=data["total_cost_time"],
            avg_cost_time=data["avg_cost_time"],
            remaining_quota=data.get("remaining_quota")
        )

    async def get_api_config(self) -> ApiConfig:
        """获取API配置信息"""
        result = await self._send_request("GET", "config")
        data = result["data"]
        return ApiConfig(
            max_file_size=data["max_file_size"],
            supported_formats=data["supported_formats"],
            rate_limit=data["rate_limit"]
        )

    # ========== 流式接口 ==========

    async def stream_task_pages(
            self,
            task_id: str,
            page_size: int = 20
    ) -> AsyncGenerator[PageItem, None]:
        """流式获取所有页面（自动翻页）"""
        page = 1

        while True:
            pagination = await self.get_task_page(task_id, page=page, page_size=page_size)

            if not pagination.items:
                break

            for item in pagination.items:
                yield item

            if page >= pagination.total_pages:
                break

            page += 1

    # ========== 批量处理辅助 ==========

    async def process_multiple(
            self,
            sources: List[Union[str, Path]],
            max_concurrency: int = 5,
            **kwargs
    ) -> List[Dict[str, Any]]:
        """并发处理多个文档（带限流）"""
        semaphore = asyncio.Semaphore(max_concurrency)
        results = []

        async def process_one(source):
            async with semaphore:
                try:
                    return await self.parse(source, **kwargs)
                except Exception as e:
                    return {"error": str(e), "source": source}

        tasks = [process_one(src) for src in sources]
        return await asyncio.gather(*tasks, return_exceptions=False)
