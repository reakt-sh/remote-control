# Use the official NanoMQ base image
FROM emqx/nanomq:0.19.0

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y cmake git openssl libssl-dev pkg-config build-essential --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Clone the NanoMQ repository
RUN git clone https://github.com/emqx/nanomq.git /tmp/nanomq
WORKDIR /tmp/nanomq
RUN git checkout 0.19.0

# Create build directory
RUN mkdir build
WORKDIR /tmp/nanomq/build

# Configure CMake with TLS support
RUN cmake -DWITH_TLS=ON ..

# Build NanoMQ
RUN make

# Install NanoMQ
RUN make install

# Clean up build files
RUN rm -rf /tmp/nanomq

# Copy custom configuration file (if you have one)
COPY /home/rcd/Desktop/Workspace/remote-control/central-server/NanoMQ/nanomq.conf /etc/nanomq.conf
COPY /etc/letsencrypt/archive/wt.rtsys-lab.de/fullchain1.pem /etc/fullchain1.pem
COPY /etc/letsencrypt/archive/wt.rtsys-lab.de/chain1.pem /etc/chain1.pem
COPY /etc/letsencrypt/archive/wt.rtsys-lab.de/privkey1.pem /etc/privkey1.pem

# Expose MQTT ports
EXPOSE 1883 8883 8081 8083 8084

# Start NanoMQ
CMD ["nanomq", "start", "--conf", "/etc/nanomq.conf"]