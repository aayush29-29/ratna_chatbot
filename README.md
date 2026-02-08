# Ratna Chatbot

Flask chatbot for Shree Ratna Rajya Laxmi Secondary School, powered by Google Gemini AI.

## Deploy on Render

1. **Push this repo to GitHub** (ensure `.env` is not committed; it's in `.gitignore`).

2. **Create a Web Service on [Render](https://dashboard.render.com)**  
   - **New → Web Service**  
   - Connect your GitHub repo and select this project.

3. **Configure the service**
   - **Runtime:** Python 3  
   - **Build Command:** `pip install -r requirements.txt`  
   - **Start Command:** `gunicorn -b 0.0.0.0:$PORT app:app`

4. **Environment variables** (Dashboard → Environment)
   - `GEMINI_API_KEY` – Your [Google AI Studio](https://aistudio.google.com/apikey) API key (required for chat).  
   - `SECRET_KEY` – A long random string for Flask sessions (Render can generate one; or use `python -c "import secrets; print(secrets.token_hex(32))"`).

5. **Deploy**  
   Render will build and deploy. Your app will be available at `https://<your-service>.onrender.com`.

## Local development

```bash
# Create virtualenv (optional)
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env with GEMINI_API_KEY=your_key

# Run
python app.py
```

Open http://localhost:5000 (or the port shown in the terminal).

## Note on Render free tier

User accounts and feedback are stored in `users.json` and `feedbacks.txt` on the server filesystem. On Render’s free tier the disk is ephemeral, so this data can be reset on redeploy. For production you may want to use a database (e.g. PostgreSQL on Render).
