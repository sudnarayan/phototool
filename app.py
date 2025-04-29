import streamlit as st
from PIL import Image
import io
import stripe
from streamlit_cropper import st_cropper

# --- App Config ---
st.set_page_config(page_title="BLS Canada Photo Tool", layout="centered")
st.title("BLS Canada Photo Tool")

# Load Stripe keys and app URL
secret_stripe = st.secrets.get("stripe", {})
stripe_secret = secret_stripe.get("secret_key")
stripe_pub = secret_stripe.get("publishable_key")
app_url = st.secrets.get("app", {}).get("url", "https://blsphoto.streamlit.app/")
if stripe_secret:
    stripe.api_key = stripe_secret

# Workflow tabs
tabs = st.tabs(["Photo Tool", "Payment", "Feedback"])

# --- Tab 1: Photo Tool ---
with tabs[0]:
    st.header("Other Services")
    service = st.selectbox("Select Service Type", ["Passport", "OCI", "Visa", "Other Services"])
    dpi = st.selectbox("Output DPI for printing", [150, 200, 300], index=2)
    uploaded = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])
    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Original Photo", use_column_width=True)
        box = st_cropper(img, aspect_ratio=(1,1))
        if box:
            # Calculate output size in px
            # Example: 210px square (fixed), or use dpi to calculate inches-based
            size_px = 210
            resized = box.resize((size_px, size_px), Image.Resampling.LANCZOS)
            st.image(resized, caption=f"Resized Preview ({size_px}×{size_px} px)", use_column_width=False)
            buf = io.BytesIO()
            resized.save(buf, format="JPEG")
            st.download_button(
                label=f"Download Resized Photo",
                data=buf.getvalue(),
                file_name=f"bls_{service.lower().replace(' ', '_')}_{size_px}px.jpg",
                mime="image/jpeg"
            )
    else:
        st.info("Choose a photo above to start cropping and resizing.")

# --- Tab 2: Payment ---
with tabs[1]:
    st.header("Secure Payment")
    if not stripe_secret or not stripe_pub:
        st.error("⚠️ Stripe keys not found. Add `stripe.secret_key` and `stripe.publishable_key` to `.streamlit/secrets.toml`.")
    params = st.query_params
    if params.get("success"):
        st.success("🎉 Payment successful! You can now download full-resolution photos.")
        st.session_state.paid = True
    elif params.get("canceled"):
        st.error("Payment canceled. Please retry to unlock downloads.")
    else:
        st.info("A $1.99 fee unlocks full download functionality. Secure payment via Stripe.")
    if stripe_secret and stripe_pub and not st.session_state.get("paid"):
        if st.button("Pay $1.99 USD Now"):
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": "BLS Photo Tool Service Fee"},
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

# --- Tab 3: Feedback ---
with tabs[2]:
    st.header("Feedback")
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    feedback = st.text_area("Tell us what you think or report issues")
    if st.button("Submit Feedback"):
        # In real app: send to email or database
        st.success("Thanks for your feedback! We appreciate it.")

# Footer
st.markdown("---")
st.caption("Built for BLS Canada users — DIY and keep your cash!")
