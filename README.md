# OptiBot Mini Clone

Customer support chatbot scraper and vector store manager for OptiSigns.com.

## Setup

### Prerequisites
- Python 3.11+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone repository
git clone <optisigns>
cd <optisigns>

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.sample .env
# Edit .env and add your OPENAI_API_KEY
```

### Initial Setup (One-time)

```bash

# 1. Scrape articles and upload to vector store
python scraper.py
python vector_store_manager.py

# 2. Test full pipeline
python main.py
```

## How to Run Locally

```bash
# Run scraper and uploader
python main.py

# Docker (alternative)
docker build -t optibot-scraper .
docker run --env-file .env optibot-scraper
```

**Example output:**
```
============================================================
Upload Summary
============================================================
✓ Uploaded: 30
✗ Failed:   0
━ Total:    30

Vector Store Statistics
============================================================
File Counts:
  - Total:       30
  - Completed:   30
  
Estimated Chunks: ~75 chunks
  (Based on 30 files × ~2.5 chunks/file)
  Chunk size: 800 tokens, overlap: 400 tokens
============================================================
```

## Daily Job Deployment

**GitHub Actions Workflow**: Runs daily at 2:00 AM UTC

- **Logs**: [View latest run](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
- **Manual trigger**: Actions tab → "Daily Article Scrape and Upload" → Run workflow

The job automatically:
1. Re-scrapes articles from support.optisigns.com
2. Detects changes (MD5 hash comparison)
3. Uploads only new/updated articles (delta)
4. Logs counts: added, updated, skipped

## Assistant Test Results

![Playground Screenshot](screenshot.png)

**Test question**: "How do I add a YouTube video?"

**Response**: Assistant correctly answered with:
- Step-by-step instructions
- Citations to source articles
- Article URLs for reference

[View full test in OpenAI Playground](https://platform.openai.com/playground/assistants)

## Architecture

**Scraper** (`scraper.py`)
- Uses Zendesk public API
- Converts HTML to clean Markdown
- MD5 hash-based change detection

**Vector Store Manager** (`vector_store_manager.py`)
- API-based upload (no UI)
- Uploads only changed files
- Logs upload statistics

**Main Pipeline** (`main.py`)
- Orchestrates: scrape → detect changes → upload
- Docker support
- GitHub Actions integration

**Chunking Strategy**: OpenAI default (800 tokens, 400 overlap)

### Why This Strategy?

OpenAI's automatic chunking is optimized for file_search:

**Chunk Size: 800 tokens**
- Balances context preservation and retrieval precision
- ~600 words per chunk (typical support article paragraph)
- Maintains coherent semantic units

**Overlap: 400 tokens (50%)**
- Prevents information loss at chunk boundaries
- Ensures questions matching boundary content find relevant chunks
- Critical for multi-step instructions that span chunks

**Example**: A 2000-token article (typical length) creates:
- ~3 chunks with overlap
- Each chunk contains full context from adjacent chunks
- Search queries retrieve all relevant sections

**Logging**: The system logs:
- Total files uploaded (e.g., 30 files)
- Estimated chunks created (~75 chunks for 30 articles)
- File processing status (completed/in_progress/failed)

## Environment Variables

```bash
OPENAI_API_KEY=sk-proj-xxxxx     # OpenAI API key
VECTOR_STORE_ID=vs_xxxxx         # Created by setup_assistant.py
ASSISTANT_ID=asst_xxxxx          # Created by setup_assistant.py
```

## Implementation Notes

**Scraping**: Uses Zendesk public API to fetch articles from support.optisigns.com. Preserves links, code blocks, and headings while removing navigation/ads.

**Change Detection**: MD5 hashing ensures only modified articles are uploaded, reducing API costs and processing time.

**Assistant Prompt** (verbatim as required):
```
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
```

## Project Structure

```
├── .github/workflows/daily-scrape.yml    # GitHub Actions
├── articles/                             # Scraped markdown files
├── scraper.py                            # Zendesk API scraper
├── vector_store_manager.py               # OpenAI API uploader
├── main.py                               # Main orchestrator
├── Dockerfile                            # Container definition
├── requirements.txt                      # Dependencies
└── .env.sample                           # Environment template
```

---

**Created for OptiSigns Back-End Technical Assessment**  
**Author**: [Your Name] | **Date**: January 2026