
# Intelligent-Student

**Intelligent-Student** is an application leveraging **Retrieval-Augmented Generation (RAG)** to provide intelligent query responses over documents.

- **LLM**: Generation mode `qwen/qwen3-32b` via Groq API.  
- **Embeddings**: `nomic-embed-text` locally through Ollama.  
- **Database**: PostgreSQL with `pgvector` extension (running in Docker).  
- **Authentication**: Only authenticated users can call API endpoints.  
- **Authorization**: Users must be authorized for a project to query its documents.  
- **User History**: The system tracks query history per user per project.  
- **Tokens**: Login generates two tokens — **access token** (short-lived) and **refresh token** (long-lived).  
- **Flexibility**: Switch models as long as they follow OpenAI API standards by updating your `.env` file.


## 1. Setup

### 1.1 Install dependencies
- Install **Docker**.  
  - On Windows, install **WSL2** first.  

- Create a Python virtual environment (example using Conda):
```bash
conda create -n istud python=3.12
conda activate istud
````

* Copy environment files and update credentials:

```bash
mv src.env.example .env
mv docker.env.example .env
# Edit .env to set API keys and other values
```

* Install Python requirements:

```bash
cd src
pip install -r requirements.txt
```

### 1.2 Start Docker services

```bash
cd docker
docker compose up
```

### 1.3 Apply database migrations

```bash
cd src
alembic upgrade head
```

### 1.4 Start the FastAPI app

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

Your app will be running at `http://localhost:5000`.

---

## 2. API Routes

### **2.1 Auth** (`/auth`)

User authentication, authorization, token management, and role updates.

| Endpoint       | Method | Description                       |
| -------------- | ------ | --------------------------------- |
| `/signup`      | POST   | Register a new user               |
| `/login`       | POST   | Authenticate user & get tokens    |
| `/refresh`     | POST   | Refresh access token              |
| `/logout`      | POST   | Log out and invalidate tokens     |
| `/authorize`   | POST   | Grant permissions                 |
| `/deauthorize` | POST   | Revoke permissions                |
| `/update-role` | POST   | Update a user's role (admin only) |

---

### **2.2 Projects** (`/projects`)

Manage projects, assign users, and retrieve project information.

| Endpoint  | Method | Description            |
| --------- | ------ | ---------------------- |
| `/`       | POST   | Create a new project   |
| `/`       | GET    | List all projects      |
| `/search` | GET    | Search project by name |
| `/`       | PUT    | Update project details |
| `/`       | DELETE | Delete a project       |

---

### **2.3 Documents** (`/documents`)

Upload, process, manage, and search documents for RAG queries.

| Endpoint                 | Method | Description                               |
| ------------------------ | ------ | ----------------------------------------- |
| `/upload/{project_name}` | POST   | Upload one or multiple files to a project |
| `/process`               | POST   | Process documents to generate embeddings  |
| `/flush`                 | POST   | Flush document embeddings                 |
| `/delete`                | POST   | Delete specific documents                 |
| `/`                      | GET    | List documents for a project              |
| `/search`                | POST   | Search a document by project and filename |

---

### **2.4 Query** (`/query`)

Send queries to the RAG engine and retrieve answers.
```
Authorization: Only users authorized for a specific project can query its documents. Attempting to query a project without permission will return an authorization error.
```

| Endpoint | Method | Description                                          |
| -------- | ------ | ---------------------------------------------------- |
| `/`      | POST   | Query a project and get top-K results from documents |

**Example Request:**

```json
POST /query
{
  "project_name": "my_project",
  "query": "Explain RAG workflow",
  "k": 5
}
```

---

### **2.5 System** (`/system`)

System management and health endpoints.

| Endpoint | Method | Description                     |
| -------- | ------ | ------------------------------- |
| `/reset` | POST   | Reset the system (internal use) |

---

## 3. Notes

* Make sure your models, API keys, and database URLs in `.env` match your environment.
* Docker is required to run Postgres with `pgvector` for vector storage.
* You can replace LLMs and embeddings with any OpenAI-compatible model by updating `.env`.
 