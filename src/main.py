from fastapi import FastAPI, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Annotated
from threading import Lock
from pydantic import BaseModel, Field, TypeAdapter
import json
from fastapi.templating import Jinja2Templates
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(title="App Shelf", description="内网软件分发服务")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class AppModel(BaseModel):
    id: Annotated[str, Field(description="软件唯一标识符")]
    name: Annotated[str, Field(description="软件名称")]
    description: Annotated[str, Field(description="软件描述")]
    category: Annotated[str, Field(description="软件分类")]
    icon: Annotated[str, Field(description="软件图标")]
    version: Annotated[str, Field(description="软件版本")]
    size: Annotated[str, Field(description="软件大小")]
    publisher: Annotated[str, Field(description="软件发行商")]

class AppManager:
    def __init__(self, apps_json: Path):
        self.apps_json = apps_json
        self.lock = Lock()
        self.reload_apps()

    def reload_apps(self):
        if not self.apps_json.exists():
            self.apps = []
            return
        with self.lock:
            try:
                apps = json.loads(self.apps_json.read_text(encoding="utf-8"))
                validated_apps = TypeAdapter(list[AppModel]).validate_python(apps)
                self.apps = validated_apps
                logger.info(f"Loaded {len(self.apps)} apps")
                self.app_dict = {app.id: app for app in self.apps}
            except Exception as e:
                logger.error(f"Error loading apps: {e}")
                self.apps = []
                self.app_dict = {}

    def get_apps(self) -> list[AppModel]:
        return self.apps

    def get_app(self, app_id: str) -> AppModel | None:
        return self.app_dict.get(app_id)

app_manager = AppManager(Path("apps.json"))

@app.get("/api/apps/{app_id}", response_model=AppModel)
def get_app(app_id: str):
    app = app_manager.get_app(app_id)
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="软件不存在")
    return app

@app.get("/api/apps", response_model=list[AppModel])
def get_apps():
    return app_manager.get_apps()

@app.post("/reload-apps")
def reload_apps():
    app_manager.reload_apps()
    return {"message": "软件列表已重新加载"}

@app.get("/")
def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")
