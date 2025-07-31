FROM emqx/nanomq:0.19.0

# Just copy your config and certificates
COPY /home/rcd/Desktop/Workspace/remote-control/central-server/NanoMQ/nanomq.conf /etc/nanomq.conf
COPY /etc/letsencrypt/archive/wt.rtsys-lab.de/fullchain1.pem /etc/fullchain1.pem
COPY /etc/letsencrypt/archive/wt.rtsys-lab.de/chain1.pem /etc/chain1.pem
COPY /etc/letsencrypt/archive/wt.rtsys-lab.de/privkey1.pem /etc/privkey1.pem

EXPOSE 1883 8883 8081 8083 8084
CMD ["nanomq", "start", "--conf", "/etc/nanomq.conf"]