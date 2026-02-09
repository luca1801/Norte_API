# API Norte - Quick Start

# 1. Setup environment
Copy-Item .env.example .env

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the API
python main.py

# API will be available at:
# - http://localhost:8000
# - Docs: http://localhost:8000/docs
