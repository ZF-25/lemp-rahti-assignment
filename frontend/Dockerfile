FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/
COPY docs.html /usr/share/nginx/html/
COPY docs-images /usr/share/nginx/html/docs-images/

# Remove the default server configuration.
RUN rm -f /etc/nginx/conf.d/default.conf \
    && chgrp -R 0 /var/cache/nginx /var/run /etc/nginx /usr/share/nginx/html \
    && chmod -R g=u /var/cache/nginx /var/run /etc/nginx /usr/share/nginx/html

EXPOSE 8080