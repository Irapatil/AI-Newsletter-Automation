# Technology Stack

## Frontend

| Layer | Technology | Purpose |
|---|---|---|
| UI Framework | React 18 | Component-based chat-first console |
| Language | TypeScript | Type-safe frontend code, mirrored against backend Pydantic schemas |
| Styling | Tailwind CSS | Utility-first styling, dark-mode-default enterprise theme |
| Build Tool | Vite | Dev server + production bundling |
| Component Primitives | Radix UI (shadcn/ui pattern) | Accessible, unstyled primitives (dialog, tabs, tooltip, etc.) |
| Animation | Framer Motion | LangGraph execution animation, panel transitions |
| Markdown Rendering | React Markdown + remark-gfm | Executive summary rendering |
| Data Fetching | TanStack React Query | Caching, polling (health, Outlook delivery status), mutations |
| HTTP Client | Axios | Typed API client with centralized error handling |
| Icons | Lucide React | Icon set throughout the console |

## Backend

| Layer | Technology | Purpose |
|---|---|---|
| Web Framework | FastAPI 0.115 | Async REST API, OpenAPI/Swagger-first |
| Language | Python 3.11+ | Backend implementation language |
| Data Validation | Pydantic v2 | Request/response schemas, settings validation |
| Configuration | pydantic-settings | Environment-variable-driven configuration |
| ASGI Server | Uvicorn | Production/development server |
| Orchestration | LangGraph | Deterministic multi-agent `StateGraph` workflow |
| LLM Integration | LangChain (`langchain`, `langchain-openai`, `langchain-core`) | Provider-agnostic chat/embeddings client abstraction |
| LLM Provider | OpenAI GPT-4o | Executive summary, per-article summaries, subject line generation |
| Embeddings | OpenAI Embeddings (`text-embedding-3-small`) | Semantic search / deduplication vectors |
| HTTP Client | httpx | Outbound calls to external source APIs |
| Retry Logic | tenacity | Exponential backoff on transient HTTP failures |
| Templating | Jinja2 | HTML newsletter rendering |
| Markdown Generation | markdown2 | Markdown newsletter rendition |
| Logging | structlog | Structured, environment-aware logging (colorized text in dev, JSON elsewhere) |
| Feed Parsing | feedparser | RSS/Atom ingestion for news collectors |
| HTML Parsing | BeautifulSoup4 | Source content extraction where needed |

## AI / Semantic Search

| Layer | Technology | Purpose |
|---|---|---|
| Summarization | OpenAI GPT-4o (via LangChain) | Executive summary, per-article summaries, subject line |
| Embeddings | OpenAI Embeddings API | Vector representation of article title + snippet |
| Semantic Search | Cosine similarity over embeddings | Near-duplicate detection across publishers |
| Mock Provider | Deterministic hash-based embeddings + extractive text | Offline/CI-safe execution with zero API dependency |

## Automation & Delivery

| Layer | Technology | Purpose |
|---|---|---|
| Scheduling & Orchestration | Microsoft Power Automate | Daily trigger, HTTP orchestration, delivery callback |
| Email Delivery | Office 365 Outlook connector ("Send an email V2") | Actual email transport to the distribution list |

## External Data Sources

| Layer | Technology | Purpose |
|---|---|---|
| News Feeds | RSS (via feedparser) | Publisher and per-company news collection |
| News Search | NewsAPI | Supplemental global news and policy search |
| Code/OSS Trends | GitHub API | Trending repository discovery |
| Model Hub | Hugging Face Hub API | Open-source model release tracking |
| Research Papers | arXiv API | AI/ML research paper discovery |
| Funding Data | Crunchbase API (with Google News fallback) | Startup funding round tracking |
| Job Boards | Greenhouse, Lever (public APIs) | Hiring trend collection |
| Talent Data | LinkedIn provider (mock or API) | Supplemental hiring signal, pluggable for a licensed API |

## Testing & Quality Tooling

| Layer | Technology | Purpose |
|---|---|---|
| Backend Testing | pytest + pytest-cov | Unit/integration tests, coverage reporting |
| Backend Linting | ruff | Fast Python linting |
| Backend Formatting | black, isort | Code formatting and import ordering |
| Backend Type Checking | mypy | Static type checking |
| Frontend Linting | ESLint | TypeScript/React linting |
| Frontend Type Checking | tsc (TypeScript compiler) | Build-time type checking |

## Deployment

| Layer | Technology | Purpose |
|---|---|---|
| Containerization | Docker, Docker Compose | Backend + frontend container images |
| Backend Container Runtime | `python:3.11-slim` base | Production backend image |
| Frontend Container Runtime | Nginx | Static frontend serving |
