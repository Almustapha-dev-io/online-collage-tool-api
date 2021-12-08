FROM python:3.9.1-alpine3.13

WORKDIR /app

COPY Pipfile* .
RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add jpeg-dev zlib-dev libjpeg
RUN pip3 install pipenv
RUN pipenv install --ignore-pipfile --system --deploy
RUN apk del build-deps
EXPOSE 5000

COPY . .

RUN addgroup app && adduser -S -G app app
RUN mkdir /app/images /app/resized
RUN chmod o+w /app
RUN chown app:app /app/images /app/resized
USER app

CMD ["python3", "app.py"]