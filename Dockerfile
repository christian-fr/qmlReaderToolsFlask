FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine
RUN apk --update add bash nano
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/qform/static
#ENV FLASK_APP qform
COPY ./requirements.txt /var/www/requirements.txt
COPY ./qform/static /var/www/qform/static
COPY . /app
RUN pip install -r /var/www/requirements.txt