import logging.config

import yaml
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from .routers.crawl import router as crawl_router
from .routers.search import router as search_router
from .routers.extract import router as extract_router

with open("logging.yaml", encoding="utf8") as f:
    config = yaml.safe_load(f)

logging.config.dictConfig(config)


app = FastAPI(docs_url=None, redoc_url=None)

app.mount(
    "/static",
    StaticFiles(directory="./static/swagger"),
    name="static",
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


app.include_router(crawl_router)
app.include_router(search_router)
app.include_router(extract_router)