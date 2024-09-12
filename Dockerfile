FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     libstdc++6

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./

# Remove py which is pulled in by retry, py is not needed and is a CVE
RUN pip install -i https://mirrors.cloud.tencent.com/pypi/simple --no-cache-dir --upgrade -r requirements.txt && \
    pip uninstall -y py && \
    playwright install chromium && playwright install-deps chromium

COPY . ./

EXPOSE 80
CMD uvicorn ccbot.app:app --host 0.0.0.0 --port 80