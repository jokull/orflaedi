# set base image (host OS)
FROM nikolaik/python-nodejs:python3.9-nodejs20-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# set the working directory in the container
WORKDIR /code

COPY . .

# install dependencies
RUN pip install -r requirements.txt --no-cache-dir
RUN npm install -g pnpm && pnpm install && pnpm run build

# command to run on container start
CMD ["uvicorn", "orflaedi.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips", "*", "--log-level", "debug", "--reload"]
