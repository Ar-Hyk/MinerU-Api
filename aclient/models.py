"""MinerU API 数据模型"""
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from .exceptions import *

class ParseMethod(str, Enum):
    AUTO = "auto"
    OCR = "ocr"
    TXT = "txt"


class ModelVersion(str, Enum):
    VLM = "vlm"
    PIPELINE = "pipeline"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Language(str, Enum):
    CHINESE = "ch"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"

class ExtraFormat(str, Enum):
    DOCX = "docx"
    HTML = "html"
    LATEX = "latex"

@dataclass
class PageRange:
    """页码范围"""
    start: int = 0
    end: Optional[int] = None

    def to_str(self) -> str:
        if self.end:
            return f"{self.start}-{self.end}"
        return str(self.start)



class RequestData:
    """构造请求参数"""
    # 非必须。是否启动 ocr 功能，默认 false，仅对pipeline模型有效
    is_ocr: Optional[bool] = None

    # 非必须。是否开启公式识别，默认 true，仅对pipeline模型有效
    enable_formula: Optional[bool]  = None

    # 非必须。是否开启表格识别，默认 true，仅对pipeline模型有效
    enable_table: Optional[bool]  = None

    # 非必须。指定文档语言，默认 ch，仅对pipeline模型有效
    # 其他可选值列表详见：https://www.paddleocr.ai/latest/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html
    language: Optional[Language]  = None

    # 解析对象对应的数据 ID。由大小写英文字母、数字、下划线（_）、短划线（-）、英文句号（.）组成，不超过 128 个字符，可以用于唯一标识您的业务数据。
    data_id: Optional[str]  = None

    # 解析结果回调通知您的 URL，支持使用 HTTP 和 HTTPS 协议的地址。
    # 该字段为空时，您必须定时轮询解析结果。
    # callback 接口必须支持 POST 方法、UTF-8 编码、Content-Type:application/json 传输数据，以及参数 checksum 和 content。
    # 解析接口按照以下规则和格式设置 checksum 和 content，调用您的 callback 接口返回检测结果。
    # checksum：字符串格式，由用户 uid + seed + content 拼成字符串，通过 SHA256 算法生成。
    # 用户 UID，可在个人中心查询。为防篡改，您可以在获取到推送结果时，按上述算法生成字符串，与 checksum 做一次校验。
    # content：JSON 字符串格式，请自行解析反转成 JSON 对象。关于 content 结果的示例，请参见任务查询结果的返回示例，对应任务查询结果的 data 部分。
    # 说明:您的服务端 callback 接口收到 Mineru 解析服务推送的结果后，如果返回的 HTTP 状态码为 200，则表示接收成功，其他的 HTTP 状态码均视为接收失败。
    # 接收失败时，mineru 将最多重复推送 5 次检测结果，直到接收成功。重复推送 5 次后仍未接收成功，则不再推送，建议您检查 callback 接口的状态。
    callback: Optional[str]  = None

    # 随机字符串，该值用于回调通知请求中的签名。由英文字母、数字、下划线（_）组成，不超过 64 个字符，由您自定义。
    # 用于在接收到内容安全的回调通知时校验请求由 Mineru 解析服务发起。
    # 说明：当使用 callback 时，该字段必须提供。
    seed: Optional[str]  = None

    # markdown、json为默认导出格式，无须设置，该参数仅支持docx、html、latex三种格式中的一个或多个
    extra_formats: List[ExtraFormat] | None  = None

    # 指定页码范围，格式为逗号分隔的字符串。
    # 例如："2,4-6"：表示选取第2页、第4页至第6页（包含4和6，结果为 [2,4,5,6]）；
    # "2--2"：表示从第2页一直选取到倒数第二页（其中"-2"表示倒数第二页）。
    page_ranges: Optional[str]  = None

    # mineru模型版本，两个选项:pipeline、vlm，默认pipeline。
    model_version: Optional[ModelVersion]  = None


    def validate(self):
        if len(self.data_id)>128: raise ValueError("data_id不超过 128 个字符")
        if self.callback and not self.seed: raise ValueError("提供 callback 时必须指定 seed")


    @property
    def dict(self):
        result = {}
        for k, v in self.__dict__.items():
            # if v is not None:
            #     print(f"k:{k} -> {type(k)}\nv:{v} -> {type(v)}\n{'='*10}")
            if type(v) is list and type(v[0]) is FileInfo:
                result[k] = [i.dict for i in v]
            elif v is not None:
                result[k] = v
        return result

    def __repr__(self):
        name = self.__class__.__name__
        result = ""
        for k,v in self.__dict__.items():
            if type(v) is list and type(v[0]) is FileInfo:
                result += f"{k}=[{', '.join([repr(i) for i in v])}], "
            elif v is not None:
                result += f"{k}={repr(v)}, "
        return f"{name}({result.rstrip(', ')})"


class RequestUrlFile(RequestData):
    def __init__(self,**kwargs):
        # 文件 URL，支持.pdf、.doc、.docx、.ppt、.pptx、.png、.jpg、.jpeg多种格式
        self.url: Optional[str] = kwargs.pop('url')
        super().__init__(**kwargs)


class RequestUploadFiles(RequestData):

    def __init__(self, **kwargs):
        self.files: list[FileInfo] = kwargs.pop('files')
        super().__init__(**kwargs)

    # def __


@dataclass
class ExtractInfo:
    extracted_pages:int
    total_pages: int
    start_time: str  # "2025-01-20 11:43:20"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractInfo":
        return cls(data.get("extracted_pages"), data.get("total_pages"), data.get("start_time"))

@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    status: TaskStatus
    err_msg: str
    extract_progress: Optional[ExtractInfo] = None
    full_zip_url: Optional[str] = None
    model_version: Optional[ModelVersion] = None


    @classmethod
    def from_dict(cls, data: dict) -> "TaskInfo":
        return cls(
            task_id=data.get('task_id'),
            status=data.get('state'),
            err_msg=data.get('err_msg'),
            extract_progress=data.get('extract_progress', None),
            full_zip_url=data.get('full_zip_url', None),
            model_version=data.get('model_version', None)
        )

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == TaskStatus.FAILED

@dataclass
class FileInfo:
    name: str
    file_path : Optional[str] = None
    data_id: Optional[str] = None

    @property
    def dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.data_id: result["data_id"] = self.data_id
        return result


@dataclass
class PageItem:
    """分页数据项"""
    page_id: str
    content: Dict[str, Any]
    page_num: int
    create_time: datetime


@dataclass
class Pagination:
    """分页信息"""
    page: int
    page_size: int
    total: int
    total_pages: int
    items: List[PageItem]


@dataclass
class BatchTask:
    """批量任务"""
    batch_id: str
    task_ids: List[str]
    status: TaskStatus
    total: int
    completed: int
    failed: int


@dataclass
class Response:
    """通用API响应"""
    code: int
    msg: str
    data: Optional[dict] = None
    trace_id: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.code == 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Response":
        return cls(
            code=data.get("code", 9999),
            msg=data.get("msg", "解析错误"),
            trace_id=data.get("trace_id"),
            data=data.get("data")
        )

    def raise_for_status(self) -> None:
        if self.code != 0:
            raise ApiResponseError(code=self.code, msg=self.msg)

    @property
    def task_id(self):
        result = self.data.get("task_id", None)
        if result is not list: result = [result]
        return result

    @property
    def batch_id(self):
        result = self.data.get("batch_id", None)
        return result

    @property
    def file_urls(self):
        result = self.data.get("file_urls", [])
        if result is not list: result = [result]
        return result



@dataclass
class UsageStats:
    """使用统计"""
    total_calls: int
    success_calls: int
    failed_calls: int
    total_cost_time: int
    avg_cost_time: float
    remaining_quota: Optional[int] = None


@dataclass
class ApiConfig:
    """API配置信息"""
    max_file_size: int
    supported_formats: List[str]
    rate_limit: Dict[str, int]
