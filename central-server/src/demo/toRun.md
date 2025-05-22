## to generate certificate.pem and certificate.key
```
openssl req -x509 -newkey rsa:2048 -nodes -keyout certificate.key -out certificate.pem -days 365 \
  -subj "/CN=127.0.0.1" \
  -addext "subjectAltName=IP:127.0.0.1"
```

## to get the spki hash value
```
openssl x509 -pubkey -noout -in certificate.pem | \
openssl pkey -pubin -outform der | \
openssl dgst -sha256 -binary | base64
```


## to run the server
```
python3 WT_server.py /etc/ssl/quic_conf/certificate.pem /etc/ssl/quic_conf/certificate.key
```



## to run chrome client
```
google-chrome \
  --origin-to-force-quic-on=127.0.0.1:6161 \
  --ignore-certificate-errors-spki-list=YiYMyuzMaVh0vd+xmKMWNhHbTRIyjv5+q1nolUD/+Sc=
```
