import os
import io
import logging
import requests
import json
import datetime
import secrets
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash, send_file
from flask_session import Session
from PIL import Image
import stripe
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure session to use filesystem
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Configure Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Get the domain from Replit's environment variables
REPLIT_DOMAIN = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else None
REPLIT_DEV_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN', None)

# Use a simple domain handling approach for development and production
if REPLIT_DOMAIN or REPLIT_DEV_DOMAIN:
    domain = REPLIT_DEV_DOMAIN or REPLIT_DOMAIN
    YOUR_DOMAIN = domain
    PROTOCOL = "https"
else:
    YOUR_DOMAIN = 'localhost:5000'
    PROTOCOL = "http"

# Log the domain being used for debugging
logging.info(f"Using domain: {YOUR_DOMAIN} with protocol: {PROTOCOL}")

@app.route('/')
def index():
    # Always reset payment status on index page load
    if 'paid' in session:
        session['paid'] = False
        logging.info("Reset paid status to False on index page")
    
    # Initialize download counter if not present
    if 'download_count' not in session:
        session['download_count'] = 0
        logging.info("Initialized download counter to 0")
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    # Generate CSRF token if not present
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    
    # Validate content type
    if not request.content_type or 'multipart/form-data' not in request.content_type:
        return jsonify({"error": "Invalid content type"}), 400
    
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Validate file extension
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({"error": "Invalid file type. Only JPG and PNG are allowed"}), 400
    
    if file:
        try:
            # Sanitize the filename and generate a random name to prevent path traversal
            random_filename = f"{secrets.token_hex(8)}.jpg"
            
            # Open the image with PIL to validate it's actually an image
            try:
                image = Image.open(file)
                
                # Basic image validation
                if image.format not in ['JPEG', 'PNG']:
                    return jsonify({"error": "Invalid image format"}), 400
                
                # Check for reasonable dimensions before processing
                if image.width > 5000 or image.height > 5000:
                    return jsonify({"error": "Image dimensions are too large"}), 400
            except Exception as img_err:
                logging.error(f"Image validation failed: {str(img_err)}")
                return jsonify({"error": "Invalid image file"}), 400
            
            # Resize to 600x600
            resized_image = image.resize((600, 600))
            
            # Check file size and compress if necessary
            buf_check = io.BytesIO()
            resized_image.save(buf_check, format="JPEG", quality=95)
            file_size_kb = len(buf_check.getvalue()) / 1024
            
            compression_info = {}
            if file_size_kb > 240:
                compression_info["warning"] = f"Original resized photo is {round(file_size_kb, 2)} KB, exceeding BLS Canada's 240 KB max. Attempting compression..."
                for quality in range(90, 10, -10):
                    compressed_buf = io.BytesIO()
                    resized_image.save(compressed_buf, format="JPEG", quality=quality)
                    compressed_size_kb = len(compressed_buf.getvalue()) / 1024
                    if compressed_size_kb <= 240:
                        resized_image = Image.open(io.BytesIO(compressed_buf.getvalue()))
                        compression_info["success"] = f"Compressed image to {round(compressed_size_kb, 2)} KB using quality={quality}."
                        break
                else:
                    compression_info["error"] = "Unable to compress under 240 KB even at low quality. Consider uploading a simpler image."
            
            # Save the processed image to session - don't store actual file paths
            buffered = io.BytesIO()
            resized_image.save(buffered, format="JPEG")
            session['processed_image'] = buffered.getvalue()
            
            # Generate a small preview image
            small_preview = resized_image.resize((150, 150))
            preview_buffered = io.BytesIO()
            small_preview.save(preview_buffered, format="JPEG")
            preview_data = preview_buffered.getvalue()
            import base64
            preview_b64 = base64.b64encode(preview_data).decode('utf-8')
            
            return jsonify({
                "message": "Image processed successfully",
                "preview": f"data:image/jpeg;base64,{preview_b64}",
                "compression_info": compression_info,
                "csrf_token": session['csrf_token']
            })
        except Exception as e:
            logging.error(f"Error processing image: {str(e)}")
            return jsonify({"error": f"Error processing image: {str(e)}"}), 500
    
    return jsonify({"error": "Invalid file"}), 400

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        # Validate CSRF token to prevent CSRF attacks
        csrf_token = request.form.get('csrf_token', '')
        if not csrf_token or csrf_token != session.get('csrf_token', ''):
            logging.warning("CSRF token validation failed for checkout")
            return jsonify({"error": "Invalid security token"}), 403
        
        # Check if user has a processed image - don't allow checkout without it
        if 'processed_image' not in session:
            return jsonify({"error": "No processed image found. Please upload an image first."}), 400
        
        # Log the domain we're using for debugging (without revealing full domain details in logs)
        logging.info(f"Creating checkout session with domain: {YOUR_DOMAIN}")
        logging.info(f"Protocol: {PROTOCOL}")
        logging.info(f"Full URL will be: {PROTOCOL}://{YOUR_DOMAIN}/success")
        
        # Reset the 'paid' flag if it exists to avoid conflicts
        session['paid'] = False
        
        # Generate a checkout session with proper metadata
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "cad",
                        "product_data": {
                            "name": "PhotoPass Premium Download",
                            "description": "BLS Canada Compliant Passport/OCI/Visa Photo (600x600)"
                        },
                        "unit_amount": 299
                    },
                    "quantity": 1,
                }],
                mode="payment",
                client_reference_id=secrets.token_hex(16),  # Generate random reference ID
                success_url=f"{PROTOCOL}://{YOUR_DOMAIN}/success",
                cancel_url=f"{PROTOCOL}://{YOUR_DOMAIN}/cancel"
            )
            
            # Store minimal info in session - only the ID
            session['checkout_session_id'] = checkout_session.id
            
            # Generate new CSRF token for next request
            session['csrf_token'] = secrets.token_hex(16)
            
            return jsonify({
                "url": checkout_session.url,
                "csrf_token": session['csrf_token']
            })
        except Exception as stripe_error:
            logging.error(f"Stripe API Error: {str(stripe_error)}")
            return jsonify({"error": f"Payment processor error: {str(stripe_error)}"}), 500
    except Exception as e:
        logging.error(f"Error creating checkout session: {str(e)}")
        # Don't return the exact error to the client to avoid leaking implementation details
        return jsonify({"error": "Unable to create payment session. Please try again later."}), 500

@app.route('/reset-session')
def reset_session():
    """Reset session data to test payment flow"""
    # Clear specific session variables
    if 'paid' in session:
        session.pop('paid')
    if 'download_count' in session:
        session.pop('download_count')
    
    flash("Session reset successfully. Your free download is now available again.")
    logging.info("Session reset by user for testing payment flow")
    return redirect(url_for('index'))

@app.route('/success', methods=['GET', 'POST'])
def success():
    # Mark the payment as successful in the session
    session['paid'] = True
    logging.info("Payment success route accessed, setting session['paid'] = True")
    
    # Check if we have the checkout session ID
    checkout_id = session.get('checkout_session_id', 'unknown')
    
    # When a user completes payment via Stripe, they are redirected here
    logging.info(f"SUCCESS - Payment completed for checkout session: {checkout_id}")
    logging.info(f"Current session state: download_count={session.get('download_count', 0)}, paid={session.get('paid', True)}")
    
    # If this is a POST request, just confirm the payment was received
    if request.method == 'POST':
        logging.info("Received POST confirmation to /success route")
        return jsonify({"status": "payment_confirmed", "checkout_id": checkout_id})
    
    # For GET requests, show the success page
    return render_template('success.html')

@app.route('/cancel')
def cancel():
    return render_template('cancel.html')

@app.route('/download')
def download():
    # Log download attempt for debugging
    logging.info("==== DOWNLOAD ATTEMPT ====")
    logging.info(f"Session state - download_count: {session.get('download_count', 0)}, paid: {session.get('paid', False)}")
    
    # Initialize download counter if not present
    if 'download_count' not in session:
        session['download_count'] = 0
        logging.info("Initialized download counter to 0")
    
    # Check if we have an image to download
    if 'processed_image' not in session:
        flash("No processed image found. Please upload an image first.")
        logging.info("Download failed: No processed image found")
        return redirect(url_for('index'))
    
    # Determine if this should be free or paid
    free_download = session.get('download_count', 0) < 1
    has_paid = session.get('paid', False)
    
    logging.info(f"Download permission check - Free download available: {free_download}, Has paid: {has_paid}")
    
    # If they've already used their free download and haven't paid, redirect to payment
    if not free_download and not has_paid:
        flash("You've used your free download. Please complete payment for additional downloads.")
        logging.info("Download blocked: User has already used free download and hasn't paid")
        return redirect(url_for('index'))
    
    # At this point, download is allowed
    # Increment download counter BEFORE sending the file
    current_count = session.get('download_count', 0)
    session['download_count'] = current_count + 1
    logging.info(f"Download allowed: Incremented download counter from {current_count} to {current_count + 1}")
    
    # Create a BytesIO object from the stored image
    img_io = io.BytesIO(session['processed_image'])
    img_io.seek(0)
    
    # Log clear download status
    if free_download:
        logging.info("FREE DOWNLOAD provided to user")
    else:
        logging.info("PAID DOWNLOAD provided to user")
    
    return send_file(
        img_io,
        mimetype='image/jpeg',
        as_attachment=True,
        download_name='bls_photo.jpg'
    )

def save_feedback_to_file(name, feedback, email=None, timestamp=None):
    """Save feedback data to a local JSON file"""
    # Create timestamp if not provided
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare feedback data
    feedback_data = {
        "timestamp": timestamp,
        "name": name,
        "email": email if email else "Not provided",
        "feedback": feedback
    }
    
    try:
        # Ensure the feedback directory exists
        os.makedirs('feedback', exist_ok=True)
        
        # Save to a JSON file in the feedback directory
        feedback_file = os.path.join('feedback', 'feedback_records.json')
        
        # Read existing feedback if file exists
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r') as f:
                    all_feedback = json.load(f)
            except json.JSONDecodeError:
                # If file is corrupted, start with empty list
                all_feedback = []
        else:
            all_feedback = []
        
        # Add new feedback to the list
        all_feedback.append(feedback_data)
        
        # Write the updated feedback list back to the file
        with open(feedback_file, 'w') as f:
            json.dump(all_feedback, f, indent=2)
        
        logging.info(f"Feedback saved to file: {feedback_file}")
        return True
    
    except Exception as e:
        logging.error(f"Error saving feedback to file: {str(e)}")
        return False

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    # Validate CSRF token
    csrf_token = request.form.get('csrf_token', '')
    if not csrf_token or csrf_token != session.get('csrf_token', ''):
        logging.warning("CSRF token validation failed")
        return jsonify({"error": "Invalid or missing security token"}), 403
    
    # Sanitize and validate input
    name = request.form.get('name', '').strip()
    feedback = request.form.get('feedback', '').strip()
    email = request.form.get('email', '').strip()
    
    # Validate input
    if not name or not feedback:
        return jsonify({"error": "Name and feedback are required"}), 400
        
    # Basic length validation to prevent abuse
    if len(name) > 100 or len(feedback) > 2000:
        return jsonify({"error": "Input exceeds maximum allowed length"}), 400
    
    # Simple email validation if provided
    if email and ('@' not in email or '.' not in email):
        return jsonify({"error": "Invalid email format"}), 400
    
    try:
        # Sanitize inputs to prevent injection attacks
        name = name.replace('<', '&lt;').replace('>', '&gt;')
        feedback = feedback.replace('<', '&lt;').replace('>', '&gt;')
        if email:
            email = email.replace('<', '&lt;').replace('>', '&gt;')
        
        # Log the feedback with sanitized values
        logging.info(f"Feedback received - Name: {name}, Email: {email and email[:3] + '***' or 'Not provided'}")
        
        # Save feedback to a file using our helper function
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_success = save_feedback_to_file(name, feedback, email, timestamp)
        
        # Store in session for confirmation page - only if has email
        if email:
            session['feedback_email'] = email
            session['feedback_name'] = name
        
        # Generate new CSRF token for next request
        session['csrf_token'] = secrets.token_hex(16)
        
        # Return success response
        return jsonify({
            "message": "Feedback submitted successfully", 
            "auto_response": True if email else False,
            "feedback_saved": save_success,
            "csrf_token": session['csrf_token']
        })
        
    except Exception as e:
        logging.error(f"Error submitting feedback: {str(e)}")
        return jsonify({"error": "An error occurred while processing your feedback"}), 500

@app.route('/feedback-confirmation')
def feedback_confirmation():
    """Render a feedback confirmation page with auto-response"""
    name = session.get('feedback_name', '')
    email = session.get('feedback_email', '')
    
    # Clear the session variables after use
    if 'feedback_email' in session:
        session.pop('feedback_email')
    if 'feedback_name' in session:
        session.pop('feedback_name')
        
    return render_template('feedback_confirmation.html', name=name, email=email)

# Security settings

# Environment variables for sensitive info
# You can change this admin password to anything you'd like for better security
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'blsphoto123')

# Secret key for session encryption - generate a strong random key
if not app.secret_key:
    app.secret_key = secrets.token_hex(32)

@app.route('/admin/logout')
def admin_logout():
    """Logout from admin panel"""
    if 'admin_authenticated' in session:
        session.pop('admin_authenticated')
    return redirect(url_for('index'))

@app.route('/admin/feedback', methods=['GET', 'POST'])
def view_feedback():
    """Admin page to view all feedback submissions with password protection"""
    # Check if user is already authenticated
    if session.get('admin_authenticated'):
        try:
            feedback_file = os.path.join('feedback', 'feedback_records.json')
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r') as f:
                    feedback_data = json.load(f)
                
                # Sort feedback by timestamp (newest first)
                feedback_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                return render_template('admin_feedback.html', feedback=feedback_data)
            else:
                return render_template('admin_feedback.html', feedback=[], error="No feedback found")
        except Exception as e:
            logging.error(f"Error viewing feedback: {str(e)}")
            return render_template('admin_feedback.html', feedback=[], error=str(e))
    
    # If not authenticated, show login form
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            return redirect(url_for('view_feedback'))
        else:
            return render_template('admin_login.html', error="Invalid password. Please try again.")
    
    return render_template('admin_login.html')

@app.route('/direct-payment', methods=['POST'])
def direct_payment():
    """Process direct payment (for testing in Replit environment)"""
    # Validate CSRF token
    csrf_token = request.form.get('csrf_token', '')
    if not csrf_token or csrf_token != session.get('csrf_token', ''):
        logging.warning("CSRF token validation failed for direct payment")
        return jsonify({"error": "Invalid security token"}), 403
    
    # Mark the payment as successful
    session['paid'] = True
    logging.info("Direct payment processed, setting session['paid'] = True")
    
    # Return success with updated CSRF token
    session['csrf_token'] = secrets.token_hex(16)
    return jsonify({
        "status": "success",
        "message": "Payment processed successfully",
        "csrf_token": session['csrf_token']
    })

@app.route('/payment-status')
def payment_status():
    # Generate CSRF token if not exists
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    
    download_count = session.get('download_count', 0)
    free_download_available = download_count < 1
    
    # Return current payment status with CSRF token
    return jsonify({
        "paid": session.get('paid', False),
        "download_count": download_count,
        "free_download_available": free_download_available,
        "csrf_token": session.get('csrf_token')
    })

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    # Prevent browsers from detecting the type of a response if the Content-Type header is not set
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevents the browser from rendering the page if it detects a cross-site scripting attack
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Control how much information the browser includes with referrers
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Prevent page from being framed (clickjacking protection)
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Content Security Policy - restrict resources loaded by the browser
    csp = "default-src 'self'; "
    csp += "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    csp += "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com 'unsafe-inline'; "
    csp += "img-src 'self' https://images.unsplash.com data:; "
    csp += "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
    csp += "connect-src 'self'; "
    csp += "frame-src 'self' https://js.stripe.com; "
    response.headers['Content-Security-Policy'] = csp
    
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
