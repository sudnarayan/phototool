# SnapVisa - Passport Photo App

This Streamlit app helps users upload, resize, preview, and purchase passport photos compatible with BLS Canada requirements.

## Features
- Upload and auto-resize to 600x600px
- Tiny preview to avoid misuse
- Stripe payment integration
- Feedback saved to Google Sheets via Google Forms

## How to Run Locally
1. Install dependencies:
    pip install -r requirements.txt
2. Set your Stripe keys in `.streamlit/secrets.toml` or via Streamlit Cloud secrets
3. Run:
    streamlit run app.py
