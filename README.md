secure api copied from: https://github.com/MohamedKari/secure-flask-container-template


# On the remote host
```
git clone https://github.com/christian-fr/qmlReaderToolsFlask qmlReaderToolsFlask && cd qmlReaderToolsFlask
echo DOMAIN_NAME=$DOMAIN_NAME >> .env 
echo EMAIL_ADDRESS=$MAIL_ADDRESS >> .env
echo FLASK_USER=$FLASK_USER >> .env
echo FLASK_PW_HASH=$FLASK_PW_HASH >> .env
docker-compose -f docker-compose.initial.yml up --build # initial certbot run
docker-compose up --build # startup the container
```
