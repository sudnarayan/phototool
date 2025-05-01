import streamlit as st
from PIL import Image
import io
import stripe

# Stripe Key from Streamlit Cloud Secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# App layout
st.set_page_config(page_title="SnapVisa - DIY Passport Photo")
st.title("📸 SnapVisa - BLS Canada Passport Photo Maker")

if "paid" not in st.session_state:
    st.session_state.paid = False

uploaded_file = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Photo", use_column_width=True)

    resized_image = image.resize((600, 600))
    st.image(resized_image, caption="Resized to 600x600 (BLS Canada Spec)")

    # Payment logic
    if not st.session_state.paid:
        st.subheader("Download for $2.99 CAD")
        if st.button("💳 Pay with Stripe"):
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "cad",
                        "product_data": {"name": "BLS Photo 600x600"},
                        "unit_amount": 299
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=st.secrets["SUCCESS_URL"],
                cancel_url=st.secrets["CANCEL_URL"]
            )
            st.write(f"[👉 Complete Payment Here]({session.url})", unsafe_allow_html=True)

    # Post-payment image download
    if st.query_params.get("paid") == ["true"]:
        st.session_state.paid = True

    if st.session_state.paid:
        st.success("✅ Payment verified. Ready to download!")
        buf = io.BytesIO()
        resized_image.save(buf, format="JPEG")
        st.download_button("📥 Download Photo", data=buf.getvalue(), file_name="bls_photo.jpg", mime="image/jpeg")

# Feedback section
st.markdown("---")
with st.form("feedback"):
    st.subheader("💬 Feedback")
    name = st.text_input("Your Name")
    message = st.text_area("What should we improve?")
    if st.form_submit_button("Submit"):
        st.success("Thanks for helping improve SnapVisa!")

st.info("💡 Tip: Use a white wall, direct lighting, and keep your face straight!")
