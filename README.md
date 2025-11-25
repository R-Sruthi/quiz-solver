# LLM-Powered Quiz Solver

An automated system that solves data analysis quizzes using Claude AI and headless browser automation.

## Project Structure
```
quiz-solver/
├── main.py                 # FastAPI server
├── quiz_solver.py          # Core quiz solving logic
├── data_processor.py       # Data processing utilities
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── Dockerfile             # Docker configuration
├── test_endpoint.py       # Testing script
└── README.md              # This file
```

## Features

- ✅ Automated quiz solving with Claude AI
- ✅ Headless browser rendering with Playwright
- ✅ Multi-format data processing (PDF, CSV, Excel, JSON)
- ✅ Chained quiz navigation
- ✅ Automatic answer submission
- ✅ 3-minute response time handling

## Setup Instructions

### 1. Clone and Install
```bash
# Clone your repository
git clone <your-repo-url>
cd quiz-solver

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Fill in:
- `STUDENT_EMAIL`: Your email from Google Form
- `STUDENT_SECRET`: Your secret string from Google Form
- `ANTHROPIC_API_KEY`: Your Claude API key from console.anthropic.com

### 3. Run Locally
```bash
# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Test the endpoint
python test_endpoint.py
```

### 4. Deploy

Choose one platform:

#### Railway (Easiest)
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

#### Render
1. Push code to GitHub
2. Connect repo to Render
3. Add environment variables
4. Deploy

## Testing
```bash
# Local test (requires running server + credentials)
python test_endpoint.py

# Quick local verification (mocks dependencies, no credentials needed)
python3 test_api_local.py

# Or with curl
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "secret": "your-secret",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

## Google Form Submission

Submit these to the Google Form:
1. Email address
2. Secret string
3. System prompt (≤100 chars) - to protect code word
4. User prompt (≤100 chars) - to extract code word
5. API endpoint URL (your-deployed-url.com/solve)
6. GitHub repo URL (public with MIT LICENSE)


Your endpoint must:
- Respond within 3 minutes
- Handle chained quizzes
- Process PDFs, CSVs, Excel files
- Submit correct answers

## License

MIT License
