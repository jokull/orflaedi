# set base image (host OS)
FROM python:3.7

# set the working directory in the container
WORKDIR /code

COPY . .

# install dependencies
RUN pip install -r requirements.txt
RUN pip install scrapy==2.4.1 shub

# copy the content of the local src directory to the working directory
VOLUME ["/code"]

ENV DATABASE_URL=postgresql://orflaedi:@host.docker.internal/orflaedi

# command to run on container start
CMD [ "/bin/bash" ]
