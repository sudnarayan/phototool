
import streamlit as st
from PIL import Image
import io
import stripe
import requests

# Stripe key from Streamlit Cloud secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

st.set_page_config(page_title="SnapVisa - BLS Canada Passport Photo")
st.title("📸 SnapVisa - DIY Passport Photo for BLS Canada")

if "paid" not in st.session_state:
    st.session_state.paid = False

uploaded_file = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Photo", use_container_width=True)

    resized_image = image.resize((600, 600))

    with st.expander("🔍 Tiny Preview of Resized Photo (600x600)", expanded=False):
        small_preview = resized_image.resize((150, 150))
        st.image(small_preview, caption="(Preview only)", use_container_width=False, output_format="JPEG", clamp=True)

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

    if st.query_params.get("paid") == ["true"]:
        st.session_state.paid = True

    if st.session_state.paid:
        st.success("✅ Payment verified. Ready to download!")
        buf = io.BytesIO()
        resized_image.save(buf, format="JPEG")
        st.download_button("📥 Download Passport Photo", data=buf.getvalue(), file_name="bls_photo.jpg", mime="image/jpeg")

# Feedback form and Google Sheets integration
def send_feedback_to_google_form(name, feedback):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfuzQAKXWhTociKZ-cS-M0XPMVj_AQuNE7EMXwv7JTrb1mJTA/formResponse"
    data = {
        "entry.1272137688": name,
        "entry.657457410": feedback
    }
    response = requests.post(form_url, data=data)
    return response.status_code

st.markdown("---")
with st.form("feedback"):
    st.subheader("💬 Feedback")
    name = st.text_input("Your Name")
    message = st.text_area("What should we improve?")
    if st.form_submit_button("Submit"):
        status = send_feedback_to_google_form(name, message)
        if status == 200:
            st.success("✅ Feedback submitted to Google Sheets!")
        else:
            st.warning("⚠️ Failed to submit. Try again later.")

st.info("💡 Tip: Use a white wall, straight face, and soft lighting for best passport photo results.")
