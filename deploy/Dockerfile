# Builds Forgevia even when the platform's Root Directory is set to ./deploy
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm sudo curl unzip git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn beautifulsoup4 httpx python-multipart lxml
RUN useradd -r -M -s /usr/sbin/nologin fvrun && useradd -m -u 1000 app && echo "app ALL=(fvrun) NOPASSWD: ALL" > /etc/sudoers.d/app && chmod 440 /etc/sudoers.d/app
WORKDIR /home/app/forgevia
ARG REPO=https://github.com/hassanmazhar18/forgevia
ARG CACHE_BUST=1
RUN git clone --depth 1 $REPO /tmp/src && cp -r /tmp/src/. . && rm -rf /tmp/src .git
RUN mkdir -p data && chown -R app:app /home/app && chmod 711 /home/app /home/app/forgevia
USER app
ENV FV_DATA=/home/app/forgevia/data PORT=8000
EXPOSE 8000
CMD ["sh","-c","python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
