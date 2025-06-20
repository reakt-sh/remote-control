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

## to Configure Secured Connection on remote droplet
```
sudo apt update
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/vue-app
# add following code to that file
--------------------------------------------------------------------
server {
    listen 80;
    server_name 209.38.218.207;
    return 301 https://$server_name$request_uri;  # Redirect HTTP → HTTPS
}

server {
    listen 443 ssl;
    server_name 209.38.218.207;

    # SSL Configuration
    ssl_certificate /etc/ssl/quic_conf/certificate.pem;      # Your certificate
    ssl_certificate_key /etc/ssl/quic_conf/certificate.key; # Your private key

    # Security settings (recommended)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Proxy to your Vue.js dev server (running on port 8080)
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # FastAPI WebSocket Backend (port 8000)
    location /ws/ {
        proxy_pass http://localhost:8000;  # FastAPI running on port 8000
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;

        # Timeout settings for persistent connections
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}

----------------------------------------------------------------------
sudo ln -s /etc/nginx/sites-available/vue-app /etc/nginx/sites-enabled
sudo nginx -t  # Test the config
sudo systemctl restart nginx
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


