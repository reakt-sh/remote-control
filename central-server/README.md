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
sudo certbot certonly --standalone -d rtsys-lab.de -d www.rtsys-lab.de -d speedtest.rtsys-lab.de
sudo openssl x509 -in /etc/letsencrypt/live/rtsys-lab.de/fullchain.pem -text -noout | grep DNS
```

### to Configure Secured Connection on remote droplet
```
sudo apt update
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/rtsys-lab.de
# add following code to that file
--------------------------------------------------------------------
# HTTP to HTTPS redirect for all domains
server {
    listen 80;
    listen [::]:80;
    server_name rtsys-lab.de www.rtsys-lab.de speedtest.rtsys-lab.de;
    return 301 https://$host$request_uri;
}

# Main Vue.js application (HTTPS + HTTP/2)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    server_name rtsys-lab.de www.rtsys-lab.de;

    ssl_certificate /etc/letsencrypt/live/rtsys-lab.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rtsys-lab.de/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass https://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# OpenSpeedTest Server
server {
    listen 443 ssl http2;
    server_name speedtest.rtsys-lab.de;

    ssl_certificate /etc/letsencrypt/live/rtsys-lab.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rtsys-lab.de/privkey.pem;

    client_max_body_size 100m; # Allow large POST requests
    gzip off; # Disable compression
    proxy_buffering off; # Disable proxy buffering

    # CORS headers - must be in server or location context
    location / {
        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://localhost:8080' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;

        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }

        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Disable caching
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # API routes
    location /api {
        proxy_pass http://127.0.0.1:3000/api;
        proxy_set_header Host $host;
    }
}
----------------------------------------------------------------------
sudo ln -s /etc/nginx/sites-available/vue-app /etc/nginx/sites-enabled
sudo nginx -t  # Test the config
sudo systemctl restart nginx
```

### Run OpenSpeedTest service
```
 sudo apt update
 sudo apt install docker.io -y
 sudo systemctl enable docker
 sudo systemctl start docker

 # Without CORS
 sudo docker run --restart=unless-stopped --name=openspeedtest -d -p 3000:3000 -p 3001:3001 openspeedtest/latest

 # Enable CORS
 sudo docker run --restart=unless-stopped \
  --name=openspeedtest \
  -d \
  -p 3000:3000 \
  -p 3001:3001 \
  -e ENABLE_CORS=true \
  -e CORS_ORIGINS="https://localhost:8080,https://rtsys-lab.de,https://localhost:3000,https://speedtest.rtsys-lab.de" \
  openspeedtest/latest

 sudo ufw allow 3000/tcp
 sudo ufw allow 3001/tcp
 sudo ufw reload
 ```
### Run Central Server
```
python src/main.py
```


## 🧑‍💻 Coding Conventions & 🗂️ File Naming Structure

### ✅ General Conventions
- Follow [PEP 8](https://peps.python.org/pep-0008/) for coding style.
- Use [type hints](https://peps.python.org/pep-0484/) wherever possible.
- Use [Variable Annotations](https://peps.python.org/pep-0526/) wherever possible.
- Keep functions small and focused on a single responsibility.
- Use **async/await** where applicable to leverage FastAPI's asynchronous capabilities.
- Use meaningful names for variables, functions, and classes.




### 📄 File Naming Conventions
- All **Python files and directories**: `snake_case`
- All **Pydantic schemas**: Singular, PascalCase (`UserCreate`, `ItemUpdate`)
- All **SQLAlchemy models**: Singular, PascalCase (`User`, `Item`)
- All **routes and services**: `snake_case.py`
- Use consistent prefixes/suffixes like:
  - `*_schema.py` for Pydantic models
  - `*_service.py` for business logic
  - `*_model.py` for database models
  - `*_test.py` for tests

### 🔁 Example Naming
| Component       | Example                  |
|----------------|--------------------------|
| API Route File | `users.py`               |
| Service File   | `user_service.py`        |
| Schema File    | `user_schema.py`         |
| Model File     | `user_model.py`          |
| Test File      | `test_user.py`           |

---

Following these conventions ensures a consistent, scalable, and maintainable codebase.


