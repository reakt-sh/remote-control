# CentralServer

## Setup the environment
### Generate Certificates
```
# for Local setup
openssl req -x509 -newkey rsa:2048 -nodes -keyout certificate.key -out certificate.pem -days 365 -subj "/CN=127.0.0.1" -addext "subjectAltName=IP:127.0.0.1"

# for Remote Droplet
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certificate.key \
    -out certificate.pem \
    -subj "/CN=209.38.218.207" \
    -addext "subjectAltName=IP:209.38.218.207"
```

# generate trusted TLS certificate
sudo certbot certonly --standalone -d wt.rtsys-lab.de

### Get the spki hash value
```
openssl x509 -pubkey -noout -in certificate.pem | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64
```

### Run chrome client on Mac
```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --ignore-certificate-errors-spki-list=5Q5Qbo1MT9UH92OkjjOkb89GlAiREgWWU+fvxcQTqxk=
```

### Run chrome client on Windows
```
Start-Process "chrome.exe" -ArgumentList @(
     "--origin-to-force-quic-on=127.0.0.1:4437",
     "--ignore-certificate-errors-spki-list=NwqV5COETZa+hbwbH5QbXBv+YBUbQz0+pvvXYYTJ0AQ=",
     "--ignore-certificate-errors",  # Bypass all cert errors (less secure)
     "--enable-logging",  # Helps debug
     "--v=1"  # Verbose logging
 )

```

### Run chrome client on Linux
```
# When Server is on Local machine
google-chrome --ignore-certificate-errors-spki-list=YiYMyuzMaVh0vd+xmKMWNhHbTRIyjv5+q1nolUD/+Sc=

# When Server is on Remote Droplet
google-chrome --ignore-certificate-errors-spki-list=5Q5Qbo1MT9UH92OkjjOkb89GlAiREgWWU+fvxcQTqxk=
```

### Generate certificate to access publicly
```
// Easy renewal
sudo systemctl stop nginx
sudo certbot renew --force-renewal
sudo systemctl start nginx

// Or Create new certificates
sudo certbot certonly --standalone -d rtsys-lab.de -d www.rtsys-lab.de -d speedtest.rtsys-lab.de -d wt.rtsys-lab.de -d influxdb.rtsys-lab.de -d mongodb.rtsys-lab.de

// Check the expiry dates
sudo openssl x509 -in ./fullchain.pem -noout -dates
```

### to Configure Secured Connection on remote droplet
```
sudo apt update
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/rtsys-lab.de

# Now Copy the content from nginx/rtsys-lab.de

sudo ln -s /etc/nginx/sites-available/vue-app /etc/nginx/sites-enabled
sudo nginx -t  # Test the config
sudo systemctl restart nginx
```

### Setup Venv
```
# Setup venv
sudo apt update
sudo apt install python3-venv -y
python3 -m venv rc_venv

# Activation
source /home/reaktor/Python_venv/rc_venv/bin/activate

# Deactivation
deactivate
```

### Run Central Server
```
python src/main.py
```


