FROM python:3

WORKDIR /app

RUN apt update && apt install -y graphviz-dev python3-pydot

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=qform

COPY . .

CMD [ "python", "-m", "qform.qform"]
