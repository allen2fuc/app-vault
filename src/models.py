import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, UUID, String, DateTime, JSON

class App(SQLModel, table=True):

    __tablename__ = "apps"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID, primary_key=True))
    name: str = Field(sa_column=Column(String, nullable=False))
    description: str = Field(sa_column=Column(String, nullable=True))
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False, comment="标签列表"))
    icon: str = Field(sa_column=Column(String, nullable=False, comment="图标路径"))
    version: str = Field(sa_column=Column(String, nullable=False, comment="版本号"))
    size: str = Field(sa_column=Column(String, nullable=False, comment="文件大小"))
    publisher: str = Field(sa_column=Column(String, nullable=False, comment="发行商"))
    download_url: str = Field(sa_column=Column(String, nullable=False, comment="下载地址"))
    os: str = Field(sa_column=Column(String, nullable=False, comment="支持系统 (Windows/macOS/Linux/跨平台)"))
    arch: str = Field(sa_column=Column(String, nullable=False, comment="支持架构 (x64/x86/ARM64/Universal)"))
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now))
