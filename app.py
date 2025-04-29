import streamlit as st
from PIL import Image
import io
import stripe
from streamlit_cropper import st_cropper

# --- App Config ---
st.set_page_config(page_title="BLS Canada Photo Tool", layout="centered")
st.title("BLS Canada Photo Tool")
st.markdown("""
Upload and crop your photo to meet BLS Canada requirements (OCI, passport, visa, etc.) in seconds – then download and print yourself to save up to **$8–$10** per session vs in-store services!
""")

# Load Stripe secrets and app URL
secret_stripe = st.secrets.get("stripe", {})
stripe_secret = secret_stripe.get("secret_key")
stripe_pub = secret_stripe.get("publishable_key")
app_url = st.secrets.get("app", {}).get("url", "https://blsphoto.streamlit.app/")
if stripe_secret:
    stripe.api_key = stripe_secret

# Workflow tabs
tabs = st.tabs(["1. Upload & Crop", "2. Resize & Download", "3. Instructions & Print", "4. Payment"])

# --- Tab 1: Upload & Crop ---
with tabs[0]:
    st.header("1. Upload & Crop")
    uploaded = st.file_uploader("Choose your photo (JPEG/PNG)", type=["jpg","jpeg","png"])
    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Original Photo", use_column_width=True)
        box = st_cropper(img, aspect_ratio=(1,1))
