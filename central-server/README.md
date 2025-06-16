# CentralServer

## Setup the environment
### Generate certificate.pem and certificate.key
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

### Get the spki hash value
```
openssl x509 -pubkey -noout -in certificate.pem | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64
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
google-chrome --origin-to-force-quic-on=127.0.0.1:4437 --ignore-certificate-errors-spki-list=YiYMyuzMaVh0vd+xmKMWNhHbTRIyjv5+q1nolUD/+Sc=

# When Server is on Remote Droplet
google-chrome --ignore-certificate-errors-spki-list=5Q5Qbo1MT9UH92OkjjOkb89GlAiREgWWU+fvxcQTqxk=
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


