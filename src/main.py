import logging
from typing import Annotated, Optional, Generator, TypedDict, cast
from contextlib import asynccontextmanager

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from sqlmodel import Field, create_engine, Session, select, SQLModel
from sqlalchemy import Engine

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from .models import App

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    DB_PATH: str = "sqlite:///data/appvault.db"
    DB_ECHO: bool = False

    model_config = ConfigDict(env_file=".env")

settings = Settings()
logger.info(f"Database path: {settings.DB_PATH}")

class State(TypedDict):
    engine: Engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine(settings.DB_PATH, echo=settings.DB_ECHO, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    logger.info("Application started")

    yield State(engine=engine)
    
    engine.dispose()
    logger.info("Application stopped")

app = FastAPI(title="AppVault", description="内网软件分发服务", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class AppBase(BaseModel):
    name: Annotated[str, Field(description="软件名称")]
    description: Annotated[str, Field(description="软件描述")]
    tags: Annotated[list[str], Field(description="标签列表")]
    icon: Annotated[str, Field(description="图标路径")]
    version: Annotated[str, Field(description="版本号")]
    size: Annotated[str, Field(description="文件大小")]
    publisher: Annotated[str, Field(description="发行商")]
    download_url: Annotated[str, Field(description="下载地址")]
    os: Annotated[str, Field(description="支持系统 (Windows/macOS/Linux/跨平台)")]
    arch: Annotated[str, Field(description="支持架构 (x64/x86/ARM64/Universal)")]

class AppRead(AppBase):
    id: Annotated[uuid.UUID, Field(description="软件ID")]
    created_at: Annotated[datetime, Field(description="创建时间")]
    updated_at: Annotated[datetime, Field(description="更新时间")]

class AppCreate(AppBase):
    pass

class AppUpdate(BaseModel):
    name: Annotated[Optional[str], Field(description="软件名称")]
    description: Annotated[Optional[str], Field(description="软件描述")]
    tags: Annotated[Optional[list[str]], Field(description="标签列表")]
    icon: Annotated[Optional[str], Field(description="图标路径")]
    version: Annotated[Optional[str], Field(description="版本号")]
    size: Annotated[Optional[str], Field(description="文件大小")]
    publisher: Annotated[Optional[str], Field(description="发行商")]
    download_url: Annotated[Optional[str], Field(description="下载地址")]
    os: Annotated[Optional[str], Field(description="支持系统 (Windows/macOS/Linux/跨平台)")]
    arch: Annotated[Optional[str], Field(description="支持架构 (x64/x86/ARM64/Universal)")]


def get_db(request: Request) -> Generator[Session, None, None]:
    state: State = cast(State, request.state)
    with Session(state.engine) as session:
        yield session


@app.get("/")
def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/admin")
def get_admin(request: Request):
    return templates.TemplateResponse(request, "admin.html")


@app.get("/api/apps", response_model=list[App])
def list_apps(tag: str | None = None, os: str | None = None, arch: str | None = None, q: str | None = None, session: Session = Depends(get_db)):
    conditions = []
    if tag:
        conditions.append(App.tags.contains([tag]))
    if os:
        conditions.append(App.os == os)
    if arch:
        conditions.append(App.arch == arch)
    if q:
        conditions.append(App.name.contains(q) | App.description.contains(q))
    return session.exec(select(App).where(*conditions).order_by(App.created_at.desc())).all()

@app.get("/api/apps/{app_id}", response_model=AppRead)
def get_app(app_id: uuid.UUID, session: Session = Depends(get_db)):
    return session.get(App, app_id)

@app.post("/api/apps", response_model=AppRead, status_code=status.HTTP_201_CREATED)
def create_app(data: AppCreate, session: Session = Depends(get_db)):
    app = App(**data.model_dump())
    session.add(app)
    session.commit()
    session.refresh(app)
    return app

@app.put("/api/apps/{app_id}", response_model=AppRead)
def update_app(app_id: uuid.UUID, data: AppUpdate, session: Session = Depends(get_db)):
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="软件不存在")
    raw = data.model_dump(exclude_none=True)
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无更新字段")
    for key, value in raw.items():
        setattr(app, key, value)
    session.commit()
    session.refresh(app)
    return app


@app.delete("/api/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(app_id: uuid.UUID, session: Session = Depends(get_db)):
    app = session.get(App, app_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="软件不存在")
    session.delete(app)
    session.commit()
    return {"message": "软件已删除"}
