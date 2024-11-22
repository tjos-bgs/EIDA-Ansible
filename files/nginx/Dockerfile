FROM nginx:stable-alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*
RUN rm -rf /etc/nginx/conf.d/*

# Alpine image links log files to stdout and stderr - undo this
RUN unlink /var/log/nginx/access.log && unlink /var/log/nginx/error.log

# Add NGINX config
COPY etc_nginx_confd/nginx.conf /etc/nginx/nginx.conf
COPY etc_nginx_confd/eida.conf /etc/nginx/conf.d/eida.conf

# Add landing page
COPY html /usr/share/nginx/html

EXPOSE 80
CMD nginx -g "daemon off;"
