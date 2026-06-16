REPOSITORY = uhub.service.ucloud.cn/allen2fuc/app-shelf:latest

dev:
	uv run uvicorn src.main:app --reload --port 8000

build:
	docker build -t ${REPOSITORY} .

push:
	docker push