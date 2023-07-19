FROM python:3.8-slim-buster

WORKDIR /app

ARG PORT=3128
ENV FLASK_APP "app.py"
ENV FLASK_DEBUG "1"
ENV PORT ${PORT}

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# https://stackoverflow.com/questions/35560894/is-docker-arg-allowed-within-cmd-instruction
CMD python3 -m flask run --host 0.0.0.0 --port ${PORT}
