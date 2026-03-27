from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from dotenv import load_dotenv
import os, random, uuid
from supabase import create_client
from datetime import datetime, timedelta
import re
from functools import wraps
from email_service import email_service
import cloudinary
import cloudinary.uploader
import cloudinary.api
from werkzeug.utils import secure_filename
from PIL import Image
import io
import requests
import pickle
import cv2
import numpy as np
import threading
import time
from detection_pytorch import analyze_image

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Supabase Clients
supabase_auth = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

supabase_db = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Image resize settings
THUMBNAIL_SIZE = (150, 150)
DISPLAY_SIZE = (400, 400)
QUALITY = 85

# Load the trained AI Model
class AIDetector:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.load_model()
        
    def load_model(self):
        """Load the trained Random Forest model"""
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'image_classifier.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.model_loaded = True
                print("✅ AI Model loaded successfully from image_classifier.pkl")
            else:
                print("⚠️ Model file not found. Using fallback detection.")
                self.model_loaded = False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model_loaded = False
    
    def extract_features(self, img):
        """Extract features for prediction (must match training features)"""
        # Resize to standard size
        img = cv2.resize(img, (128, 128))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Feature 1: Blur score (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Feature 2: Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size if edges.size > 0 else 0
        
        # Feature 3: Texture (standard deviation)
        texture = np.std(gray) / 255
        
        # Features 4-19: Color histograms (16 bins each for R,G,B)
        hist_r = cv2.calcHist([img], [0], None, [16], [0, 256]).flatten()
        hist_g = cv2.calcHist([img], [1], None, [16], [0, 256]).flatten()
        hist_b = cv2.calcHist([img], [2], None, [16], [0, 256]).flatten()
        
        # Features 20-21: Top/Bottom edge densities (for meme detection)
        h, w = img.shape[:2]
        top_region = edges[0:int(h*0.25), :]
        bottom_region = edges[int(h*0.75):h, :]
        top_density = np.sum(top_region > 0) / top_region.size if top_region.size > 0 else 0
        bottom_density = np.sum(bottom_region > 0) / bottom_region.size if bottom_region.size > 0 else 0
        
        # Feature 22: Meme feature (difference between top and bottom density)
        meme_feature = abs(top_density - bottom_density)
        
        # Feature 23: Aspect ratio
        aspect = w / h
        
        # Combine all features
        features = np.concatenate([
            [blur_score / 1000],  # Normalize blur score
            [edge_density],
            [texture],
            hist_r,
            hist_g,
            hist_b,
            [top_density],
            [bottom_density],
            [meme_feature],
            [aspect]
        ])
        
        return features.reshape(1, -1)
    
    def detect_intentional_blur(self, img):
        """Check if blur is intentional (portrait mode)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
        
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face_region = gray[y:y+h, x:x+w]
                if len(face_region) > 0:
                    face_blur = cv2.Laplacian(face_region, cv2.CV_64F).var()
                    # If face is sharp but overall image is blurry, it's intentional
                    if face_blur > 100:
                        return True, "Portrait mode - face is sharp, background blurred"
        return False, "Accidental blur - no clear subject"
    
    def detect(self, image_bytes):
        """Main detection function"""
        try:
            # Load image from bytes
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return 'normal', 0.5, 'Failed to process image'
            
            # Check if model is loaded
            if self.model_loaded and self.model:
                # Extract features
                features = self.extract_features(img)
                
                # Get prediction
                prediction = self.model.predict(features)[0]
                
                # Get confidence
                if hasattr(self.model, 'predict_proba'):
                    probs = self.model.predict_proba(features)[0]
                    classes = self.model.classes_
                    idx = list(classes).index(prediction)
                    confidence = probs[idx]
                else:
                    confidence = 0.75
                
                # Map prediction to category
                category_map = {
                    'blurred': 'blur',
                    'memes': 'meme',
                    'screenshots': 'screenshot',
                    'normal': 'normal'
                }
                
                category = category_map.get(prediction, 'normal')
                reason = f'AI detected as {prediction} with {confidence:.1%} confidence'
                
                # Special check for blur - detect if intentional
                if category == 'blur':
                    is_intentional, intentional_reason = self.detect_intentional_blur(img)
                    if is_intentional:
                        return 'normal', 0.85, intentional_reason
                
                return category, confidence, reason
            else:
                # Fallback detection using OpenCV only
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Blur detection
                blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                if blur_score < 100:
                    # Check if intentional blur
                    is_intentional, _ = self.detect_intentional_blur(img)
                    if is_intentional:
                        return 'normal', 0.8, 'Portrait mode - keep'
                    return 'blur', 0.7, f'Blurry image (score: {blur_score:.0f})'
                
                # Screenshot detection by aspect ratio
                h, w = img.shape[:2]
                aspect = w / h
                if abs(aspect - 16/9) < 0.1 or abs(aspect - 9/16) < 0.1:
                    # Check top region for UI elements
                    top = img[0:int(h*0.08), :]
                    gray_top = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
                    edges_top = cv2.Canny(gray_top, 50, 150)
                    edge_density = np.sum(edges_top > 0) / edges_top.size
                    if edge_density > 0.05:
                        return 'screenshot', 0.65, 'UI elements detected'
                
                # Meme detection
                top_edges = edges[0:int(h*0.25), :]
                bottom_edges = edges[int(h*0.75):h, :]
                top_density = np.sum(top_edges > 0) / top_edges.size if top_edges.size > 0 else 0
                bottom_density = np.sum(bottom_edges > 0) / bottom_edges.size if bottom_edges.size > 0 else 0
                if top_density > 0.03 and bottom_density > 0.03:
                    return 'meme', 0.6, 'Text pattern detected'
                
                return 'normal', 0.8, 'Good quality image'
                
        except Exception as e:
            print(f"Detection error: {e}")
            return 'normal', 0.5, 'Detection failed'

# Initialize detector
detector = AIDetector()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_datetime_safe(dt_string):
    """Safely parse datetime string from Supabase"""
    try:
        if dt_string.endswith('+00:00'):
            dt_string = dt_string.replace('+00:00', '')
        if dt_string.endswith('Z'):
            dt_string = dt_string.replace('Z', '')
        return datetime.fromisoformat(dt_string)
    except:
        return datetime.utcnow()

def resize_image_for_gallery(image_bytes, target_size=DISPLAY_SIZE):
    """Resize image for gallery display"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=QUALITY, optimize=True)
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        print(f"Image resize error: {e}")
        return image_bytes

def resize_thumbnail(image_bytes, target_size=THUMBNAIL_SIZE):
    """Create thumbnail"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        if img.size[0] != img.size[1]:
            new_img = Image.new('RGB', target_size, (255, 255, 255))
            offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
            new_img.paste(img, offset)
            img = new_img
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=75, optimize=True)
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        print(f"Thumbnail resize error: {e}")
        return image_bytes

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Log user activity
def log_user_activity(user_id, action_type, action_details=None):
    try:
        log_data = {
            "user_id": user_id,
            "action_type": action_type,
            "action_details": action_details or {}
        }
        supabase_db.table("user_activity_log").insert(log_data).execute()
    except Exception as e:
        print(f"Failed to log activity: {e}")

# Ensure user exists
def ensure_user_exists(user_id, email=None, name=None):
    try:
        user_check = supabase_db.table("users").select("id").eq("id", user_id).execute()
        
        if not user_check.data:
            if not email:
                try:
                    auth_user = supabase_auth.auth.admin.get_user_by_id(user_id)
                    if auth_user:
                        email = auth_user.email
                        name = auth_user.user_metadata.get('full_name', email.split('@')[0])
                except:
                    pass
            
            user_data = {
                "id": user_id,
                "email": email or f"user_{user_id}@temp.com",
                "full_name": name or "User",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            supabase_db.table("users").insert(user_data).execute()
            return True
        return True
    except Exception as e:
        print(f"Error ensuring user exists: {e}")
        return False

# ==================== EMAIL SCHEDULING ====================

def send_cleanup_reminders():
    print("\n Running cleanup reminder scheduler...")
    try:
        users = supabase_db.table("users") \
            .select("id, email, full_name") \
            .eq("is_active", True) \
            .execute()
        
        if not users.data:
            return
        
        reminder_count = 0
        for user in users.data:
            try:
                flagged = supabase_db.table("cleanup_items") \
                    .select("id") \
                    .eq("user_id", user['id']) \
                    .eq("user_recovered", False) \
                    .eq("user_approved_deletion", False) \
                    .in_("predicted_category", ['blur', 'meme', 'screenshot']) \
                    .execute()
                
                if flagged.data and len(flagged.data) > 0:
                    email_service.send_cleanup_reminder(
                        to_email=user['email'],
                        name=user['full_name'],
                        flagged_count=len(flagged.data)
                    )
                    reminder_count += 1
                    print(f"Reminder sent to {user['email']} - {len(flagged.data)} flagged images")
                    
            except Exception as e:
                print(f"Error sending reminder to {user.get('email')}: {e}")
        
        print(f"Sent {reminder_count} cleanup reminders")
        
    except Exception as e:
        print(f"Reminder scheduler error: {e}")

def send_monthly_reports():
    print("\n Running monthly report scheduler...")
    try:
        users = supabase_db.table("users") \
            .select("id, email, full_name") \
            .eq("is_active", True) \
            .execute()
        
        if not users.data:
            print("No active users found")
            return
        
        print(f"Sending reports to {len(users.data)} users...")
        report_count = 0
        
        for user in users.data:
            try:
                last_month = datetime.utcnow() - timedelta(days=30)
                
                items = supabase_db.table("cleanup_items") \
                    .select("predicted_category, user_approved_deletion, user_recovered, created_at") \
                    .eq("user_id", user['id']) \
                    .gte("created_at", last_month.isoformat()) \
                    .execute()
                
                if items.data:
                    total_uploaded = len(items.data)
                    deleted = sum(1 for i in items.data if i.get('user_approved_deletion'))
                    recovered = sum(1 for i in items.data if i.get('user_recovered'))
                    flagged = sum(1 for i in items.data if i.get('predicted_category') in ['blur', 'meme', 'screenshot'])
                    
                    if total_uploaded > 0 or flagged > 0:
                        email_service.send_monthly_report(
                            to_email=user['email'],
                            name=user['full_name'],
                            stats={
                                'total_uploaded': total_uploaded,
                                'deleted': deleted,
                                'recovered': recovered,
                                'flagged': flagged,
                                'remaining': total_uploaded - deleted
                            }
                        )
                        report_count += 1
                        print(f"Report sent to {user['email']}")
                        
            except Exception as e:
                print(f"Error sending report to {user.get('email')}: {e}")
        
        print(f"Sent {report_count} monthly reports")
        
    except Exception as e:
        print(f"Monthly report error: {e}")

def start_scheduler():
    def run_scheduler():
        while True:
            try:
                now = datetime.now()
                
                if now.weekday() == 0 and now.hour == 9:
                    send_cleanup_reminders()
                
                if now.day == 1 and now.hour == 10:
                    send_monthly_reports()
                
                time.sleep(3600)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(3600)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print(" Email scheduler started")

start_scheduler()

# ---------------- HOME ----------------
@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template("login.html")

# ---------------- SIGNUP API ----------------
@app.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        if not re.match(r'^[^\s@]+@([^\s@]+\.)+[^\s@]+$', email):
            return jsonify({"error": "Invalid email format"}), 400

        res = supabase_auth.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": name if name else email.split('@')[0]
                }
            }
        })

        if res.user:
            otp = str(random.randint(100000, 999999))
            expires = datetime.utcnow() + timedelta(minutes=10)
            
            supabase_db.table("otp_verifications").insert({
                "email": email,
                "otp_code": otp,
                "expires_at": expires.isoformat()
            }).execute()
            
            email_service.send_verification_email(
                to_email=email,
                name=name if name else email.split('@')[0],
                otp=otp
            )
            
            return jsonify({
                "success": True,
                "message": "Verification code sent to your email",
                "email": email
            }), 200
        else:
            return jsonify({"error": "Signup failed"}), 400
            
    except Exception as e:
        error = str(e).lower()
        if "user already registered" in error:
            return jsonify({"error": "Email already registered"}), 400
        return jsonify({"error": str(e)}), 400

# ---------------- LOGIN API ----------------
@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        res = supabase_auth.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if res.user:
            ensure_user_exists(res.user.id, res.user.email, 
                              res.user.user_metadata.get('full_name'))
            
            user_check = supabase_db.table("users") \
                .select("email_verified") \
                .eq("id", res.user.id) \
                .execute()
            
            is_verified = user_check.data[0].get('email_verified', False) if user_check.data else False
            
            if not is_verified:
                otp = str(random.randint(100000, 999999))
                expires = datetime.utcnow() + timedelta(minutes=10)
                
                supabase_db.table("otp_verifications").insert({
                    "email": email,
                    "otp_code": otp,
                    "expires_at": expires.isoformat()
                }).execute()
                
                email_service.send_verification_email(
                    to_email=email,
                    name=res.user.user_metadata.get('full_name', email.split('@')[0]),
                    otp=otp
                )
                
                return jsonify({
                    "success": False,
                    "needs_verification": True,
                    "email": email,
                    "message": "Please verify your email first. OTP sent!"
                }), 200
            
            session.permanent = True
            session['user'] = res.user.id
            session['user_email'] = res.user.email
            session['user_name'] = res.user.user_metadata.get('full_name', email.split('@')[0])
            session['email_verified'] = True
            
            supabase_db.table("users").update({
                "last_login_at": datetime.utcnow().isoformat()
            }).eq("id", res.user.id).execute()
            
            log_user_activity(res.user.id, "login", {"email": email})
            
            return jsonify({
                "success": True,
                "redirect": "/dashboard"
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        error = str(e)
        if "Invalid login credentials" in error:
            return jsonify({"error": "Invalid email or password"}), 401
        return jsonify({"error": "Login failed"}), 400

# ---------------- VERIFY OTP API ----------------
@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        password = data.get('password', '')

        if not email or not otp:
            return jsonify({"error": "Email and OTP required"}), 400

        res = supabase_db.table("otp_verifications") \
            .select("*") \
            .eq("email", email) \
            .eq("otp_code", otp) \
            .is_("verified_at", None) \
            .order("created_at", desc=True) \
            .execute()

        if not res.data:
            return jsonify({"error": "Invalid OTP code"}), 400

        valid_otp = None
        now = datetime.utcnow()
        
        for record in res.data:
            expires_at_str = record['expires_at']
            try:
                expires_at = parse_datetime_safe(expires_at_str)
            except:
                continue
                
            if expires_at > now:
                valid_otp = record
                break

        if not valid_otp:
            return jsonify({"error": "OTP expired. Please request a new one."}), 400

        supabase_db.table("otp_verifications").update({
            "verified_at": datetime.utcnow().isoformat()
        }).eq("id", valid_otp['id']).execute()
        
        supabase_db.table("users") \
            .update({"email_verified": True}) \
            .eq("email", email) \
            .execute()
        
        user_info = supabase_db.table("users") \
            .select("id, full_name") \
            .eq("email", email) \
            .execute()
        
        if user_info.data:
            user_id = user_info.data[0]['id']
            user_name = user_info.data[0].get('full_name', email.split('@')[0])
            
            email_service.send_welcome_email(email, user_name)
            log_user_activity(user_id, "email_verified", {"email": email})
            
            session.clear()
            session.permanent = True
            session['user'] = user_id
            session['user_email'] = email
            session['user_name'] = user_name
            session['email_verified'] = True
            
            return jsonify({
                "success": True,
                "redirect": "/dashboard"
            }), 200
        else:
            return jsonify({"success": True, "redirect": "/login"}), 200

    except Exception as e:
        print(f"OTP verification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

# ---------------- RESEND OTP ----------------
@app.route('/api/resend-otp', methods=['POST'])
def api_resend_otp():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({"error": "Email required"}), 400

        user_result = supabase_db.table("users") \
            .select("full_name") \
            .eq("email", email) \
            .execute()
        
        name = user_result.data[0].get('full_name', email.split('@')[0]) if user_result.data else email.split('@')[0]
        
        otp = str(random.randint(100000, 999999))
        expires = datetime.utcnow() + timedelta(minutes=10)
        
        supabase_db.table("otp_verifications") \
            .delete() \
            .eq("email", email) \
            .is_("verified_at", None) \
            .execute()
        
        supabase_db.table("otp_verifications").insert({
            "email": email,
            "otp_code": otp,
            "expires_at": expires.isoformat()
        }).execute()
        
        email_service.send_verification_email(email, name, otp)
        
        return jsonify({"success": True, "message": "New OTP sent"}), 200
        
    except Exception as e:
        print(f"Resend error: {e}")
        return jsonify({"error": str(e)}), 400

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    return render_template("dashboard.html", 
                         user_id=session['user'],
                         user_email=session.get('user_email', ''),
                         user_name=session.get('user_name', ''),
                         email_verified=session.get('email_verified', False))

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------------- GET USER STATS ----------------
@app.route('/api/user/stats')
@require_auth
def get_user_stats():
    try:
        user_id = session['user']
        
        user_result = supabase_db.table("users") \
            .select("cleanup_count, total_images_cleaned, created_at, email_verified") \
            .eq("id", user_id) \
            .execute()
        
        sessions_result = supabase_db.table("cleanup_sessions") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("started_at", desc=True) \
            .limit(5) \
            .execute()
        
        total_analyzed = sum(s.get('total_images', 0) for s in sessions_result.data) if sessions_result.data else 0
        user_data = user_result.data[0] if user_result.data else {}
        
        return jsonify({
            "success": True,
            "stats": {
                "cleanup_sessions": user_data.get('cleanup_count', 0),
                "images_cleaned": user_data.get('total_images_cleaned', 0),
                "images_analyzed": total_analyzed,
                "member_since": user_data.get('created_at'),
                "email_verified": user_data.get('email_verified', False)
            }
        }), 200
        
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- CREATE CLEANUP SESSION ----------------
@app.route('/api/cleanup/start', methods=['POST'])
@require_auth
def start_cleanup_session():
    try:
        user_id = session['user']
        
        session_data = {
            "user_id": user_id,
            "started_at": datetime.utcnow().isoformat(),
            "session_status": "active"
        }
        
        result = supabase_db.table("cleanup_sessions").insert(session_data).execute()
        
        if result.data:
            log_user_activity(user_id, "cleanup_started", {"session_id": result.data[0]['id']})
            return jsonify({"success": True, "session_id": result.data[0]['id']}), 200
        else:
            return jsonify({"error": "Failed to create session"}), 500
            
    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- UPLOAD IMAGES TO CLOUDINARY ----------------
@app.route('/api/upload-images', methods=['POST'])
@require_auth
def upload_images():
    try:
        user_id = session['user']
        
        ensure_user_exists(user_id, session.get('user_email'), session.get('user_name'))
        
        files = request.files.getlist('images')
        
        if not files:
            return jsonify({"error": "No files uploaded"}), 400
        
        uploaded_images = []
        
        for file in files:
            if file and allowed_file(file.filename):
                file.seek(0, 2)
                size = file.tell()
                file.seek(0)
                
                if size > MAX_FILE_SIZE:
                    continue
                
                original_filename = secure_filename(file.filename)
                
                # Read file bytes
                file_bytes = file.read()
                
                # RESIZE IMAGE FOR GALLERY
                resized_bytes = resize_image_for_gallery(file_bytes, DISPLAY_SIZE)
                
                # Upload resized image to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    resized_bytes,
                    folder=f"user_{user_id}",
                    resource_type="image",
                    transformation=[
                        {'quality': 'auto'},
                        {'fetch_format': 'auto'}
                    ]
                )
                
                # Get URLs
                display_url = cloudinary.utils.cloudinary_url(
                    upload_result['public_id'],
                    width=400,
                    height=400,
                    crop="limit",
                    quality="auto",
                    fetch_format="auto"
                )[0]
                
                thumbnail_url = cloudinary.utils.cloudinary_url(
                    upload_result['public_id'],
                    width=150,
                    height=150,
                    crop="fill",
                    quality="auto"
                )[0]
                
                # Store in database
                image_data = {
                    "user_id": user_id,
                    "original_filename": original_filename,
                    "file_size": len(resized_bytes),
                    "storage_path": upload_result['public_id'],
                    "predicted_category": None,
                    "confidence_score": None,
                    "reasoning": None,
                    "is_duplicate": False,
                    "recommended_for_deletion": False,
                    "user_approved_deletion": False,
                    "actually_deleted": False,
                    "user_recovered": False
                }
                
                result = supabase_db.table("cleanup_items").insert(image_data).execute()
                
                if result.data:
                    image_id = result.data[0]['id']
                    
                    uploaded_images.append({
                        "id": image_id,
                        "url": display_url,
                        "thumbnail": thumbnail_url,
                        "public_id": upload_result['public_id'],
                        "filename": original_filename
                    })
                    
                    log_user_activity(user_id, "image_uploaded", {"filename": original_filename})
        
        return jsonify({
            "success": True,
            "images": uploaded_images
        }), 200
        
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------- GET USER IMAGES ----------------
@app.route('/api/get-user-images', methods=['GET'])
@require_auth
def get_user_images():
    try:
        user_id = session['user']
        
        result = supabase_db.table("cleanup_items") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        
        images = []
        for item in result.data:
            if item['storage_path']:
                display_url = cloudinary.utils.cloudinary_url(
                    item['storage_path'],
                    width=400,
                    height=400,
                    crop="limit",
                    quality="auto",
                    fetch_format="auto"
                )[0]
                
                thumbnail_url = cloudinary.utils.cloudinary_url(
                    item['storage_path'],
                    width=150,
                    height=150,
                    crop="fill",
                    quality="auto"
                )[0]
            else:
                display_url = None
                thumbnail_url = None
            
            images.append({
                "id": item['id'],
                "url": display_url,
                "thumbnail": thumbnail_url,
                "filename": item['original_filename'],
                "predicted_category": item.get('predicted_category'),
                "confidence_score": item.get('confidence_score'),
                "user_recovered": item.get('user_recovered', False),
                "user_approved_deletion": item.get('user_approved_deletion', False),
                "upload_date": item['created_at']
            })
        
        return jsonify({
            "success": True,
            "images": images
        }), 200
        
    except Exception as e:
        print(f"Get images error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- DELETE IMAGE ----------------
@app.route('/api/image/delete', methods=['POST'])
@require_auth
def delete_image():
    try:
        user_id = session['user']
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({"error": "Image ID required"}), 400
        
        img_result = supabase_db.table("cleanup_items") \
            .select("storage_path") \
            .eq("id", image_id) \
            .eq("user_id", user_id) \
            .execute()
        
        if img_result.data:
            public_id = img_result.data[0].get('storage_path')
            if public_id:
                try:
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Cloudinary delete error: {e}")
        
        result = supabase_db.table("cleanup_items") \
            .update({
                "actually_deleted": True,
                "user_approved_deletion": True,
                "deleted_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", image_id) \
            .eq("user_id", user_id) \
            .execute()
        
        if result.data:
            log_user_activity(user_id, "image_deleted", {"image_id": image_id})
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Image not found"}), 404
            
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- RECOVER IMAGE ----------------
@app.route('/api/image/recover', methods=['POST'])
@require_auth
def recover_image():
    try:
        user_id = session['user']
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({"error": "Image ID required"}), 400
        
        result = supabase_db.table("cleanup_items") \
            .update({
                "user_recovered": True,
                "recommended_for_deletion": False
            }) \
            .eq("id", image_id) \
            .eq("user_id", user_id) \
            .execute()
        
        if result.data:
            log_user_activity(user_id, "image_recovered", {"image_id": image_id})
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Image not found"}), 404
            
    except Exception as e:
        print(f"Recover error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- BATCH DELETE ----------------
@app.route('/api/batch-delete', methods=['POST'])
@require_auth
def batch_delete():
    try:
        user_id = session['user']
        data = request.get_json()
        category = data.get('category')
        
        if not category:
            return jsonify({"error": "Category required"}), 400
        
        images = supabase_db.table("cleanup_items") \
            .select("id, storage_path") \
            .eq("user_id", user_id) \
            .eq("predicted_category", category) \
            .eq("user_recovered", False) \
            .eq("user_approved_deletion", False) \
            .execute()
        
        for img in images.data:
            if img.get('storage_path'):
                try:
                    cloudinary.uploader.destroy(img['storage_path'])
                except:
                    pass
        
        result = supabase_db.table("cleanup_items") \
            .update({
                "actually_deleted": True,
                "user_approved_deletion": True,
                "deleted_at": datetime.utcnow().isoformat()
            }) \
            .eq("user_id", user_id) \
            .eq("predicted_category", category) \
            .eq("user_recovered", False) \
            .eq("user_approved_deletion", False) \
            .execute()
        
        log_user_activity(user_id, "batch_delete", {"category": category, "count": len(images.data)})
        
        return jsonify({"success": True, "deleted_count": len(images.data)}), 200
        
    except Exception as e:
        print(f"Batch delete error: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- AI DETECTION (NEW PYTORCH DETECTOR) ----------------
@app.route('/api/detect-image', methods=['POST'])
@require_auth
def detect_image():
    try:
        user_id = session['user']
        data = request.get_json()
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({"error": "Image ID required"}), 400
        
        # Get image details
        img_result = supabase_db.table("cleanup_items") \
            .select("storage_path") \
            .eq("id", image_id) \
            .eq("user_id", user_id) \
            .execute()
        
        if not img_result.data:
            return jsonify({"error": "Image not found"}), 404
        
        storage_path = img_result.data[0]['storage_path']
        
        # Download image from Cloudinary
        image_url = cloudinary.utils.cloudinary_url(
            storage_path,
            quality="auto",
            fetch_format="auto"
        )[0]
        
        # Download image bytes
        response = requests.get(image_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download image"}), 500
        
        # Run professional detection
        category, confidence, reasoning = analyze_image(response.content)
        
        # Update database
        if category != 'normal':
            update_data = {
                "predicted_category": category,
                "confidence_score": confidence,
                "reasoning": reasoning,
                "recommended_for_deletion": True
            }
        else:
            update_data = {
                "predicted_category": None,
                "confidence_score": None,
                "reasoning": reasoning,
                "recommended_for_deletion": False
            }
        
        supabase_db.table("cleanup_items") \
            .update(update_data) \
            .eq("id", image_id) \
            .eq("user_id", user_id) \
            .execute()
        
        return jsonify({
            "success": True,
            "category": category,
            "confidence": confidence,
            "reasoning": reasoning
        }), 200
        
    except Exception as e:
        print(f"Detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------- ERROR HANDLERS ----------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)