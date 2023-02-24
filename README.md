secure api copied from: https://github.com/MohamedKari/secure-flask-container-template


# On the remote host
```
git clone https://github.com/christian-fr/qmlReaderToolsFlask qmlReaderToolsFlask && cd qmlReaderToolsFlask
echo DOMAIN_NAME=$DOMAIN_NAME >> .env 
echo EMAIL_ADDRESS=$MAIL_ADDRESS >> .env
docker-compose -f docker-compose.initial.yml up --build # obtains the initial certificate using certbot
docker-compose up --build # runs Nginx, your app, and an auto-renewal certbot
```
