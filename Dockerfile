# set base image (host OS)
FROM python:3.9-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# set the working directory in the container
WORKDIR /code

COPY . .

# Install fish
RUN apt update && apt install -y fish && rm -rf /var/lib/apt/lists/*
RUN chsh -s /usr/bin/fish
SHELL ["fish", "--command"]
ENV SHELL /usr/bin/fish

RUN pip install poetry
RUN poetry config virtualenvs.create false

# install dependencies
RUN pip install -r requirements.txt --no-cache-dir
RUN pip install scrapy==2.6.3 shub

# copy the content of the local src directory to the working directory
VOLUME ["/code"]

ENV DATABASE_URL=postgresql://orflaedi:@host.docker.internal/orflaedi

# command to run on container start
ENTRYPOINT [ "fish" ]
