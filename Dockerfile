FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=qform

COPY . .

CMD [ "python", "-m", "flask", "run", "--host=0.0.0.0"]