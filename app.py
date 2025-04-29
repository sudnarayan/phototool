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
        box = st_cropper(img, aspect_ratio=1)
        if box:
            st.session_state.cropped = box
            st.image(box, caption="Cropped Preview (1:1)", use_column_width=True)
    else:
        st.info("Upload an image to get started.")

# --- Tab 2: Resize & Download ---
with tabs[1]:
    st.header("2. Resize & Download")
    if st.session_state.get("cropped"):
        cropped = st.session_state.cropped
        resized = cropped.resize((600, 600), Image.ANTIALIAS)
        buf = io.BytesIO()
        resized.save(buf, format="JPEG")
        st.image(resized, caption="Resized 2\"×2\" Photo (600×600 px)", use_column_width=False)
        if st.session_state.get("paid"):
            st.download_button(
                label="Download Your 2\"×2\" Photo",
                data=buf.getvalue(),
                file_name="bls_passport_photo.jpg",
                mime="image/jpeg"
            )
        else:
            st.warning("Please complete payment in the Payment tab to unlock downloads.")
    else:
        st.warning("Complete Step 1 to crop your photo first.")

# --- Tab 3: Instructions & Print ---
with tabs[2]:
    st.header("3. Instructions & Best Print Route")
    st.markdown("""
1. Download your processed 2"×2" photo (600×600 px).
2. Go to **Walmart Photo Center** or any 4×6 print service.
3. Upload the JPEG and order a single **4"×6** print (contains 6 tiles).
4. Pickup same-day in-store (no extra fees).
5. Cut along the grid to get six compliant passport photos – that’s **2¢ each**!

**You just saved up to $10** vs traditional passport-photo booths.
""")

# --- Tab 4: Secure Payment ---
with tabs[3]:
    st.header("4. Secure Payment")
    # Show error if Stripe keys are missing
    if not stripe_secret or not stripe_pub:
        st.error("⚠️ Stripe keys not found. Add `stripe.secret_key` and `stripe.publishable_key` to `.streamlit/secrets.toml`.")

    # Use new query params API
    params = st.query_params
    if params.get("success"):
        st.success("🎉 Payment successful! Downloads unlocked.")
        st.session_state.paid = True
    elif params.get("canceled"):
        st.error("Payment canceled. Please retry to unlock downloads.")
    else:
        st.info("A $1.99 fee unlocks full download functionality. Secure payment via Stripe.")

    # Stripe Checkout flow
    if stripe_secret and stripe_pub and not st.session_state.get("paid"):
        if st.button("Pay $1.99 USD Now"):
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": "BLS Canada Photo Tool Service Fee"},
                            "unit_amount": 199
                        },
                        "quantity": 1
                    }],
                    mode="payment",
                    success_url=f"{app_url}?success=true",
                    cancel_url=f"{app_url}?canceled=true"
                )
                st.markdown(f"👉 [Complete Payment]({session.url})")
            except Exception as e:
                st.error(f"Payment initiation failed: {e}")

    # Footer with guidance
    st.markdown("""
---
*Built for BLS Canada users — DIY and keep your cash!*  
Set your secrets in `.streamlit/secrets.toml`:  
```toml
[stripe]
secret_key = "sk_live_..."
publishable_key = "pk_live_..."
[app]
url = "https://blsphoto.streamlit.app/"
```
""")
