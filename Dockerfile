FROM python:3.9.1-alpine3.13

WORKDIR /app

COPY Pipfile* .
RUN pip3 install pipenv
RUN pipenv install --ignore-pipfile --system --deploy

EXPOSE 5000

COPY . .

RUN addgroup app && adduser -S -G app app
RUN chown app:app /app/images /app/resized
USER app

CMD ["python3", "app.py"]