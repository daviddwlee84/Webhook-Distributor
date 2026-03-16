FROM python:3.13-slim

WORKDIR /app

ARG PORT=3128
ENV PORT=${PORT}

COPY pyproject.toml .
COPY app.py .
COPY webhooks.txt .

RUN pip3 install --no-cache-dir .

EXPOSE ${PORT}

CMD python3 app.py --host 0.0.0.0 --port ${PORT}
