FROM python:3.6

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
ADD ./sources.list /etc/apt/sources.list
RUN apt-get update \
    && apt-get install --no-install-recommends -y python3-dev libpq-dev unixodbc-dev

# install dependencies
RUN pip install --upgrade pip setuptools -i https://pypi.douban.com/simple/
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.douban.com/simple/

# copy project
COPY . /app/
