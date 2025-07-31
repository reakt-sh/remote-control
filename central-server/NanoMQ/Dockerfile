FROM emqx/nanomq:0.19.0

# Just copy your config and certificates
COPY nanomq.conf /etc/nanomq.conf
COPY fullchain1.pem /etc/fullchain1.pem
COPY chain1.pem /etc/chain1.pem
COPY privkey1.pem /etc/privkey1.pem

EXPOSE 1883 8883 8081 8083 8084
CMD ["nanomq", "start", "--conf", "/etc/nanomq.conf"]