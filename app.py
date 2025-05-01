# Final `app.py` code with Stripe payment and photo processing
app_code = """
import streamlit as st
from PIL import Image
import io
import stripe
import os

# Setup
st.set_page_config(page_title="SnapVisa - BLS Canada Photo Tool")
st.title("SnapVisa - DIY Passport Photo for BLS Canada")

# Stripe setup (replace with your actual secret key or use env variable)
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
# Session state to track if payment is completed
if 'paid' not in st.session_state:
    st.session_state.paid = False

# Upload and Resize Image
uploaded_file = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Photo', use_column_width=True)

    resized_image = image.resize((600, 600))
    st.image(resized_image, caption='Resized to BLS Canada Specs (600x600)', use_column_width=False)

    if not st.session_state.paid:
        st.subheader("Download for $2.99 CAD")
        if st.button("Proceed to Payment"):
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'cad',
                        'product_data': {
                            'name': 'BLS Canada Passport Photo',
                        },
                        'unit_amount': 299,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://blsphoto.streamlit.app/?paid=true',
                cancel_url='https://blsphoto.streamlit.app/',
            )
            st.write(f"[Pay Now]({session.url})", unsafe_allow_html=True)

    if st.query_params.get("paid") == ["true"]:
        st.session_state.paid = True

    if st.session_state.paid:
        st.success("Payment confirmed ✅")
        buf = io.BytesIO()
        resized_image.save(buf, format="JPEG")
        byte_im = buf.getvalue()
        st.download_button(label="Download JPG", data=byte_im, file_name="bls_photo.jpg", mime="image/jpeg")

# Feedback form
st.markdown("---")
with st.form("feedback_form"):
    st.subheader("Feedback")
    name = st.text_input("Name")
    feedback = st.text_area("What's one feature you'd like us to add?")
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.success("Thanks for your feedback!")

# DIY Tip
st.markdown("**Need help taking the perfect photo?** Try using a plain white wall, good lighting, and no shadows. Face the camera directly.")
"""

# Save to file
app_path = "/mnt/data/app.py"
with open(app_path, "w") as f:
    f.write(app_code)

app_path
