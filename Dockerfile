# Django 1.10.5 (pinned in requirements.txt) drops support for the
# __class__ / __classcell__ metaclass handling introduced in Python 3.8,
# so 3.7 is the newest interpreter this app actually runs on.
FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
