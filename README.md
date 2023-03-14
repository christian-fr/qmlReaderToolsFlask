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


set docker  
```
docker stop <nginx-container-name>

echo "client_max_body_size 40m;" > client_max_body_size.conf

docker run -d --name nginx-proxy -v /var/run/docker.sock:/tmp/docker.sock \
    -v <path>/client_max_body_size.conf:/etc/nginx/conf.d/client_max_body_size.conf:ro \
    -p 80:80 jwilder/nginx-proxy
    
   
     
```
