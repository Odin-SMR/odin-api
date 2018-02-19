FROM httpd

COPY odin.conf /usr/local/apache2/conf/
RUN echo "Include conf/odin.conf" >> /usr/local/apache2/conf/httpd.conf
EXPOSE 80
