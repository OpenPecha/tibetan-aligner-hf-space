FROM ghcr.io/openpecha/align-tibetan:main

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . .

CMD ["python", "app.py"]

