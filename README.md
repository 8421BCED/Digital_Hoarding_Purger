# Environment Setup Guide

To run this project correctly, you must create a `.env` file in the root directory of the project and configure all required environment variables.

---

## Step 1: Create `.env` File

In the root folder of your project, create a file named:

```
.env
```

---

## Step 2: Add Configuration

Use the template below and fill in your actual credentials:

```
# Supabase Configuration
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Flask Configuration
SECRET_KEY=

# Brevo SMTP Configuration
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

---

## Step 3: Notes

* Do not include spaces after `=`
* Do not wrap values in quotes unless required
* Keep this file private and never commit it to version control
* Ensure `.env` is listed in your `.gitignore`

---

## Step 4: Running the Application

After setting up the `.env` file, run the application:

```
python app.py
```

---

## Requirements

Make sure all dependencies are installed:

```
pip install -r requirements.txt
```

---

## Summary

This setup ensures secure handling of:

* Backend services (Supabase)
* Email system (SMTP)
* Media storage (Cloudinary)
* Application security (Flask secret key)

Proper configuration is mandatory for authentication, uploads, and email functionality to work correctly.
