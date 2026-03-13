# FastAPI Project

This is a FastAPI project configured to run in a Python virtual environment, connected to a local PostgreSQL database using Docker.

## Requirements

- **Python 3.8+**
- **pip** (Python package manager)
- **Docker Desktop** (Required to run the local database container)
- **FastAPI**, **Uvicorn**, and **SQLAlchemy**

## How to Set Up the Environment

### 1. Navigate to the Project Directory
First, ensure you are in the correct project directory:
```bash
cd TCC-MBA-API # Adjust based on your repository folder name
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory of the project and add the necessary environment variables:
```env
SECRET_KEY=your_super_secret_key_here
TEST_MODE=True
DB_URL_TEST="postgresql+asyncpg://postgres:admin@localhost:5432/faculdade-test"
```

### 3. Create the Virtual Environment
Run the following command to create the virtual environment:
```bash
python -m venv .venv
```

### 4. Activate the Virtual Environment
Activate the environment based on your terminal:
```bash
# For Windows PowerShell
.\.venv\Scripts\Activate

# For Windows Command Prompt
.venv\Scripts\activate

# For Linux/macOS
source .venv/bin/activate
```

### 5. Install Dependencies
With the virtual environment activated, install the required packages:
```bash
pip install --no-cache-dir -r requirements.txt
```

## Database Setup & Execution

### 6. Start the Local Database
Ensure Docker Desktop is running in the background. Then, start the PostgreSQL container using Docker Compose:
```bash
docker compose up -d
```

### 7. Generate Local Tables and Roles
Once the database container is running, execute the table generation script. **Note:** Run this script as a module to avoid import path issues:
```bash
python -m app.generate_table
```

### 8. Run the Server
Finally, start the FastAPI application using Uvicorn:
```bash
uvicorn app.main:app --reload
```
The application will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Documentation
Interactive API documentation (Swagger UI) will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Project Structure

```bash
.
├── app/
│   ├── main.py            # Main FastAPI application file
│   ├── core/              # Settings and configurations
│   ├── db/                # Database connections and models
│   └── generate_table.py  # Local table generation and seed script
├── docker-compose.yml     # Local database container configuration
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (ignored in version control)
├── .venv/                 # Virtual environment (ignored in version control)
└── README.md              # This file
```

## Contributing
To contribute, please fork the project, make your changes, and submit a pull request.