FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm sudo curl unzip git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn beautifulsoup4 httpx python-multipart lxml
# sandbox user for running user code
RUN useradd -r -M -s /usr/sbin/nologin fvrun && useradd -m -u 1000 app && echo "app ALL=(fvrun) NOPASSWD: ALL" > /etc/sudoers.d/app && chmod 440 /etc/sudoers.d/app
WORKDIR /home/app/forgevia
COPY --chown=app:app . .
RUN mkdir -p /home/app/forgevia/data && chown -R app:app /home/app && chmod 711 /home/app /home/app/forgevia
USER app
ENV FV_DATA=/home/app/forgevia/data PORT=8000
EXPOSE 8000
CMD ["sh","-c","python -m uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
