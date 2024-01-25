FROM php:5.6.20-fpm-alpine

WORKDIR /app

RUN docker-php-ext-install mysqli pdo pdo_mysql && docker-php-ext-enable pdo_mysql


RUN apk add --no-cache git bash

RUN echo 'date.timezone = Europe/Paris' >> /usr/local/etc/php/conf.d/timezone.ini

COPY setup.sh .

RUN chmod +x setup.sh

CMD ["./setup.sh"]
