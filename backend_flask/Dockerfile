FROM python:3.10-slim-buster

# Inside container
WORKDIR /backend_flask

# Outside container -> inside container
COPY requirements.txt requirements.txt

# Inside container
RUN pip3 install -r requirements.txt

# Outside container -> inside container
COPY . .

# Inside container
ENV FLASK_ENV=development

EXPOSE ${PORT}

# python3 -m flask run --host=0.0.0.0 --port=4567
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]