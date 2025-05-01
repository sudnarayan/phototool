# SnapVisa DIY BLS Photo Tool

This app helps users generate 2x2 inch photos as per BLS Canada requirements (for OCI, Passport, etc). Features:

- Resize to 600x600px
- Stripe-powered secure download
- Google Form feedback logger
- Official spec guide + image

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Add your secrets to `.streamlit/secrets.toml`:
   ```toml
   STRIPE_SECRET_KEY = "your_key"
   SUCCESS_URL = "https://your-app-url/?paid=true"
   CANCEL_URL = "https://your-app-url/"
   ```

3. Run:
   streamlit run app.py
