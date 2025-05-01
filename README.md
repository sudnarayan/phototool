# SnapVisa - DIY OCI / Passport Photo App (BLS Canada)

This Streamlit app helps users upload and resize photos to meet BLS Canada photo specs (e.g. OCI, passport, visa). It supports:

- ✅ Resize to 600x600 px
- ✅ File size validation and auto-compression (under 240 KB)
- ✅ Stripe payment integration
- ✅ Google Form feedback logging
- ✅ Pro printing tips (Walmart, Staples, etc.)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your Streamlit secrets:
   `.streamlit/secrets.toml`
   ```
   STRIPE_SECRET_KEY = "sk_live_..."
   SUCCESS_URL = "https://your-app-url/?paid=true"
   CANCEL_URL = "https://your-app-url/"
   ```

3. Run the app:
   ```
   streamlit run app.py
   ```

## Output

Once payment is confirmed, users can download a 600x600 JPEG photo sized for BLS Canada forms.
