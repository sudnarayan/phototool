# BLS Canada Photo Tool

**DIY 2″×2″ passport/OCI photo prep + Stripe-checkout in Streamlit**  
Save $8–$10 per session vs in-store passport services.

## Features
- **Upload & Crop** to 1:1
- **Resize** to 600×600 px (2″×2″ @ 300 DPI)
- **Stripe** payment ($1.99 unlock)
- **Download** & print (Walmart hack: 2¢ / shot)

## Local Setup
1. Clone:  
   ```bash
   git clone https://github.com/<you>/bls-photo-tool.git
   cd bls-photo-tool
   ```
2. Install deps:  
   ```bash
   pip install -r requirements.txt
   ```
3. Copy & fill secrets:  
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
4. Run:  
   ```bash
   streamlit run app.py
   ```

## Deploy
Push to Streamlit Cloud or your own server—Streamlit will auto-detect.

---

*Enjoy your passive-income-ready photo tool!* 🚀
