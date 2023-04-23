FROM 418433537685.dkr.ecr.us-east-1.amazonaws.com/cruddur-python:3.10-slim-buster

# Inside container
WORKDIR /backend_flask

# Outside container -> inside container
COPY requirements.txt requirements.txt

# Inside container
RUN pip3 install -r requirements.txt

# Outside container -> inside container
COPY . .

# Inside container
# ENV FLASK_ENV=development

# Set Enviroment Variables (Env Vars)
# Inside Container and wil remain set when the container is running
ENV FLASK_DEBUG=1

EXPOSE ${PORT}

# python3 -m flask run --host=0.0.0.0 --port=4567
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]