FROM python:3.10.8

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . .

CMD ["python", "src/main.py"]