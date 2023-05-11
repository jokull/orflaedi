# set base image (host OS)
FROM nikolaik/python-nodejs:python3.9-nodejs20-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# set the working directory in the container
WORKDIR /code

COPY . .

# install dependencies
RUN pip install -r requirements.txt --no-cache-dir
RUN npm install -g pnpm && pnpm install && pnpm run build
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install

# copy the content of the local src directory to the working directory
VOLUME ["/code"]
