# CentralServer

## Run Command
```
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
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


