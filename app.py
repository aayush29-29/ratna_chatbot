from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import os, json, datetime, time
import re

# ----------------------
# Load Environment & Configure Gemini
# ----------------------
load_dotenv()
# Prefer os.environ so Render/env vars are definitely read (not only .env)
_raw_key = (os.environ.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_API_KEY = _raw_key
if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found. Set it in Render Dashboard → Environment, then redeploy.")
else:
    print(f"✓ GEMINI_API_KEY loaded (length={len(GEMINI_API_KEY)}).")
    genai.configure(api_key=GEMINI_API_KEY)

# ----------------------
# Flask Setup
# ----------------------
app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))
app.secret_key = os.environ.get("SECRET_KEY", "chatbot-dev-change-in-production")

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
FEEDBACKS_FILE = os.path.join(os.path.dirname(__file__), "feedbacks.txt")

USERNAME_REGEX = re.compile(r'^[A-Za-z@_]+$')  # no longer used; username length only
PASSWORD_REGEX = re.compile(r'^(?=.*[A-Z])(?=.*\d)[A-Za-z0-9@_]{8,}$')

# ----------------------
# School Info Context
# ----------------------
SCHOOL_INFO = """
Shree Ratna Rajya Laxmi Secondary School is a reputed educational institution located in Nawalpur, Nepal.
It is committed to providing quality education with a perfect blend of academic excellence, moral values, and practical learning.

👨‍💻 Chatbot Creators:
This chatbot was created by Mr. Aayush Subedi and Mrs. Anjana Shrestha as an OJT (On-the-Job Training) project.
- Aayush Subedi: Grade 12 Computer Engineering student at Shree Ratna Rajya Laxmi Secondary School
  Email: aayushsubedi334@gmail.com
- Anjana Shrestha: Grade 12 Computer Engineering student at Shree Ratna Rajya Laxmi Secondary School
  Email: anjanashrestha4562@gmail.com

📍 Location:
Shree Ratna Rajya Laxmi Secondary School, Gaindakot-10, Nawalpur, Nepal.

🎓 Administration:
Principal: Mr. Nawaraj Kafle
Head of Engineering Department: Mr. Ganesh Gharti

🏫 General Information:
Established Year: 2025 B.S. (1980 A.D.)
Type: Public Community-Based School
Affiliated To: National Examination Board (NEB), Government of Nepal
Grades Offered: Nursery to Grade 12
Streams for +2 Level: Science, Management, and Computer Engineering
Computer Engineering is from class 9-12
Medium of Instruction: English and Nepali
Total Students: More than 1200 students
Total Teachers and Staff: More than 60 teachers and staff members

⏰ School Hours:
Sunday to Friday: 10:00 AM – 4:00 PM
Saturday: Closed
Break Time: 12:30 PM – 1:00 PM

📅 Important Events:
Annual Function: Every Bhadra (August/September)
Sports Week: Every Falgun (February/March)
Parents-Teachers Meeting: Every Trimester
Cultural Day: Organized once a year to promote Nepali heritage
Examination System: Unit Tests, Terminal Exams, and Final Board Exams

🎯 Motto:
"Knowledge is Power"

💻 Facilities:
- Smart Classrooms with multimedia setup
- Computer and Science Laboratories
- Library with digital and printed resources
- Playground and sports equipment
- Music, Dance, and Art Rooms
- Health and Counseling Unit
- Transportation service within Kathmandu Valley
- CCTV monitored campus for safety

👨‍🏫 Teaching Methodology:
The school focuses on project-based learning, digital education, and practical exposure.
Teachers are trained to promote creativity, teamwork, and moral discipline among students.

🏆 Achievements:
- Consistent 100% pass results in SEE examinations.
- Awarded as “Best Community Secondary School” by the Education Board in 2079 B.S.
- Students actively participate in inter-school quiz competitions, science fairs, and debates.

🌍 Extracurricular Activities:
- Sports (Football, Basketball, Volleyball, Table Tennis)
- Arts, Music, and Drama
- Debate, Quiz, and Public Speaking Clubs
- Community Service and Environmental Awareness Programs
- Scout and Red Cross Youth Circle

📬 Contact Details:
Phone: 078-402005 
Email: ratnarajya2025@gmail.com 
Website: www.ratnaschool.edu.np
Facebook: https://www.facebook.com/profile.php?id=100063770297066

Teachers and Staffs details:
1. Name: Nawaraj Kafle
   Subject: English
   Qualification: M.Ed
   Position/Class: Principal

2. Name: Lila Dhungana
   Subject: Nepali
   Qualification: M.A / B.Ed
   Class: Grade 12 (Education)

3. Name: Tak Narayan Rana
   Subject: Mathematics
   Qualification: M.Ed
   Class: Grade 10 'A'

4. Name: Chandrakanta Acharya
   Subject: Science
   Qualification: B.Sc / B.Ed
   Class: Grade 9 'A'

5. Name: Chandrakanta Bhandari
   Subject: Science
   Qualification: M.A / B.Sc
   Class: Grade 10 'B'

6. Name: Dinesh Kandel
   Subject: English
   Qualification: M.A / B.Ed
   Class: Grade 11 (Management)

7. Name: Sudan Ghimire
   Subject: Accountancy
   Qualification: MBS / B.Ed
   Class: Grade 12 (Management)

8. Name: Somnath Nyaupane
   Subject: English
   Qualification: B.A / B.Ed
   Class: Grade 8 'B'

9. Name: Narayan Prasad Kandel
   Subject: Accountancy
   Qualification: I.Sc / B.B.S

10. Name: Goma Chital
    Subject: Social Studies
    Qualification: B.Ed

11. Name: Bimala Subedi
    Subject: Mathematics
    Qualification: B.Ed
    Class: Grade 6 'A'

12. Name: Sita Devi Sharma
    Subject: Nepali
    Qualification: I.Ed
    Class: Grade 1 'B'

13. Name: Sumitra Kumari Sharma
    Subject: Mathematics
    Qualification: I.Ed
    Class: Grade 3 'B'

14. Name: Durga Prasad Nyaupane
    Subject: Nepali
    Qualification: B.A / B.Ed
    Position: Librarian

15. Name: Parbati Rijal
    Subject: English
    Qualification: M.A / B.Ed
    Class: Grade 8 'C'

16. Name: Bishnu Maya Sapkota
    Subject: Social Studies
    Qualification: M.Ed
    Class: Grade 5 'B'

17. Name: Tulasi Sharma
    Subject: English
    Qualification: I.Ed
    Class: Grade 5 'C'

18. Name: Pawan Bhattarai
    Subject: English
    Qualification: M.Ed
    Class: Grade 7 'B'

19. Name: Bikash Poudel
    Subject: Nepali
    Qualification: M.A / B.Ed
    Class: Grade 11 (Education)

20. Name: Ramesh Soti
    Subject: English
    Qualification: M.Ed
    Class: Grade 6 'B'

21. Name: Yogendra Prasad Dhungana
    Subject: English
    Qualification: M.Ed
    Class: Grade 8 'A'

22. Name: Suraksha Kandel
    Subject: English
    Qualification: +2 Education
    Class: Grade 3 'A'

23. Name: Satyata Mishra Kamal
    Subject: Social Studies
    Qualification: M.A / B.Ed
    Class: Grade 4 'B'

24. Name: Yamkala Poudel
    Subject: Science
    Qualification: BNS / B.Ed
    Class: Grade 2 'A'

25. Name: Hira Kumari Mahato
    Subject: Grade Teacher
    Qualification: B.Ed
    Class: Nursery 'A'

26. Name: Prakash Bhupal
    Subject: Mathematics
    Qualification: M.Sc Mathematics
    Class: Grade 7 'A'

27. Name: Sujina Acharya
    Subject: Accountancy
    Qualification: MBS
    Class: Grade 9 'B'

28. Name: Pratik Ghimire
    Subject: H.M.
    Qualification: B.H.M

29. Name: Ramchandra Sapkota
    Subject: English
    Qualification: B.A
    Class: Grade 4 'A'

30. Name: Navaraj Mahato
    Subject: Science
    Qualification: +2 Science

31. Name: Aksha Shrestha
    Subject: English
    Qualification: +2 Management
    Class: UKG 'A'

32. Name: Bhavana Adhikari
    Subject: Science
    Qualification: +2 Science
    Class: Grade 5 'A'


===============================
TECHNICAL & VOCATIONAL STREAM
===============================

33. Name: Er. Ganesh Bartaula
    Subject: Computer Engineering
    Qualification: BE Computer
    Position: HOD

34. Name: Shiva G.C.
    Subject: Physics
    Qualification: M.Sc Physics / B.Ed
    Class: Grade 12 (Engineering)

35. Name: Asmita Bhusal
    Subject: Chemistry
    Qualification: M.Sc Chemistry

36. Name: Er. Uday Adhikari
    Subject: Computer Engineering
    Qualification: BE Computer

37. Name: Er. Suman Adhikari
    Subject: Computer Engineering
    Qualification: BE Electronics

38. Name: Er. Nirjal Koirala
    Subject: Computer Engineering
    Qualification: BE Computer
    Class: Grade 11 (Engineering)

39. Name: Krishna Prasad Nyaupane
    Subject: Computer Engineering
    Qualification: BCA
    Class: Grade 9 'C'

40. Name: Dilliram Poudel
    Subject: Computer Engineering
    Qualification: Diploma in Computer
    Class: Grade 10 'C'

41. Name: Sagar Shrestha
    Subject: Computer
    Qualification: BCA


===============================
SCHOOL STAFF & OFFICE ASSISTANTS
===============================

42. Name: Sachin Adhikari
    Qualification: +2 Management
    Position: Office Staff (Accounts)

43. Name: Pratima Thapa
    Qualification: Bachelor of Nursing
    Position: School Nurse

44. Name: Hari Bahadur Poudel
    Qualification: Literate
    Position: Assistant Staff

45. Name: Saraswati Pathak
    Qualification: Literate
    Position: Aya

46. Name: Mina Poudel
    Qualification: Literate
    Position: Staff

47. Name: Sita Kshetri
    Qualification: Literate
    Position: Aya

48. Name: Laxmi Kandel
    Qualification: Literate
    Position: Staff

49. Name: Chandra Datt Kandel
    Qualification: Literate
    Position: Bus Driver

50. Name: Durga Thapa
    Qualification: Literate
    Position: Bus Driver

51. Name: Mohan Kumar Dhungana
    Qualification: Literate
    Position: Security Guard

52. Name: Shiva Poudel
    Qualification: +2 Hotel Management
    Position: Canteen Operator

📚 Mission:
To develop responsible, confident, and compassionate learners prepared to contribute to a changing world.

🌟 Vision:
To be recognized as a model school offering holistic education through innovation, discipline, and values.

"""


# ----------------------
# Auth System
# ----------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].strip()

        if len(username) < 8:
            flash("invalid username", "danger")
            return redirect(url_for("signup"))
        if not PASSWORD_REGEX.match(password):
            flash("choose strong password", "danger")
            return redirect(url_for("signup"))

        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        else:
            users = {}

        if username in users:
            flash("Username already exists.", "danger")
            return redirect(url_for("signup"))

        users[username] = generate_password_hash(password)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)

        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].strip()

        if len(username) < 8:
            flash("invalid username", "danger")
            return redirect(url_for("login"))
        if not PASSWORD_REGEX.match(password):
            flash("choose strong password", "danger")
            return redirect(url_for("login"))

        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        else:
            users = {}

        if username in users and check_password_hash(users[username], password):
            session["username"] = username
            session["chat_history"] = []
            flash("Login successful!", "success")
            return redirect(url_for("chatbot"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("chat_history", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/use-guest")
def use_guest():
    session.pop("username", None)
    session["guest"] = True
    session["chat_history"] = []
    flash("You are now using chatbot as guest.", "info")
    return redirect(url_for("chatbot"))

# ----------------------
# Chatbot Page
# ----------------------
@app.route("/")
def chatbot():
    if "username" not in session and "guest" not in session:
        flash("Please log in first or use as guest.", "warning")
        return redirect(url_for("login"))

    username = session.get("username") or "Guest"
    return render_template("index.html", username=username)

# ----------------------
# Env check (for debugging Render env vars – does not expose the key)
# ----------------------
@app.route("/env-check")
def env_check():
    has_key = bool(GEMINI_API_KEY)
    return jsonify({
        "gemini_configured": has_key,
        "key_length": len(GEMINI_API_KEY) if GEMINI_API_KEY else 0,
        "hint": "Redeploy after changing Environment variables on Render."
    })

# ----------------------
# Gemini AI Chat Endpoint
# ----------------------
@app.route("/get", methods=["GET"])
def get_bot_response():
    if "username" not in session and "guest" not in session:
        return jsonify({"reply": "Access denied. Please log in or use as guest."})

    user_message = request.args.get("msg", "").strip()
    if not user_message:
        return jsonify({"reply": "Please enter a message."})

    # Short, polite replies for very simple greetings (avoid long AI answers)
    simple_greetings = {
        "hi", "hi.", "hi!", "hello", "hello.", "hello!",
        "hey", "hey.", "hey!", "namaste", "namaste.", "namaste!",
        "good morning", "good morning.", "good morning!",
        "good afternoon", "good afternoon.", "good afternoon!",
        "good evening", "good evening.", "good evening!"
    }
    if user_message.lower() in simple_greetings:
        bot_reply = "Hello! How can I help you today?"

        # Save chat history and return immediately without calling Gemini
        chat_history = session.get("chat_history", [])
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": bot_reply})
        session["chat_history"] = chat_history

        return jsonify({"reply": bot_reply})

    try:
        # Get current date and time
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.strftime("%B %d, %Y")  # e.g., "January 15, 2024"
        current_time = current_datetime.strftime("%I:%M %p")  # e.g., "02:30 PM"
        current_day = current_datetime.strftime("%A")  # e.g., "Monday"
        current_datetime_full = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Check if API key is configured
        if not GEMINI_API_KEY:
            return jsonify({"reply": "⚠️ Error: Gemini API key is not configured. Set GEMINI_API_KEY in your environment (e.g. Render Dashboard → Environment)."})

        # Get conversation history for context and memory
        chat_history = session.get("chat_history", [])

        # First, list available models to find one that actually works
        model = None
        try:
            print("Listing available models...")
            all_models = list(genai.list_models())
            print(f"Total models found: {len(all_models)}")
            
            # Find models that support generateContent
            available_models = []
            for m in all_models:
                methods = getattr(m, 'supported_generation_methods', [])
                if 'generateContent' in methods:
                    model_name = m.name
                    available_models.append(model_name)
                    print(f"  ✓ {model_name} (supports generateContent)")
            
            if not available_models:
                return jsonify({"reply": "⚠️ Error: No models with generateContent support found. Please check your API key and access permissions."})
            
            # Try each available model until one works
            for avail_model in available_models:
                # Try with the model name as-is first (might include "models/" prefix)
                try:
                    print(f"Attempting to use model: {avail_model}")
                    model = genai.GenerativeModel(avail_model)
                    print(f"✓ Successfully initialized model: {avail_model}")
                    break
                except Exception as model_error:
                    print(f"✗ Model {avail_model} failed: {str(model_error)}")
                    # Try extracting just the model ID (remove "models/" prefix)
                    if "/" in avail_model:
                        model_id = avail_model.split("/")[-1]
                        try:
                            print(f"  Trying with model ID only: {model_id}")
                            model = genai.GenerativeModel(model_id)
                            print(f"✓ Successfully initialized model: {model_id}")
                            break
                        except Exception as id_error:
                            print(f"✗ Model ID {model_id} also failed: {str(id_error)}")
                    continue
            
            if model is None:
                return jsonify({"reply": f"⚠️ Error: Found {len(available_models)} models but none could be used. Please check your API key permissions."})
                
        except Exception as list_error:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error listing/initializing models: {error_details}")
            return jsonify({"reply": f"⚠️ Error: Unable to access Gemini models. Error: {str(list_error)}. Please verify your API key and model access."})

        # Enhanced system prompt for better intelligence and memory
        system_instruction = f"""You are Ratna Chatbot — an intelligent and helpful AI assistant for Shree Ratna Rajya Laxmi Secondary School, Kathmandu. You have excellent memory and can handle both school-related and general questions with intelligence and professionalism.

School info:
{SCHOOL_INFO}

Current Date and Time Information:
- Today's date: {current_date}
- Current day: {current_day}
- Current time: {current_time}
- Full datetime: {current_datetime_full}

Your personality and capabilities:
- You are intelligent, knowledgeable, and can answer general questions about science, history, geography, current events, technology, culture, and more with depth and accuracy.
- You remember previous parts of the conversation and can reference earlier topics naturally.
- You provide thoughtful, well-reasoned answers to complex questions.
- You can engage in friendly discussions, explain concepts clearly, and adapt your communication style to the user's needs.

Your tasks:
- Answer questions about the school (principal, fees, exams, events, contact info, classes, etc.) with detailed and accurate information.
- Handle general knowledge questions intelligently — provide comprehensive, accurate answers with examples when helpful.
- Reply naturally to casual chat (greetings, small talk, etc.) with warmth and professionalism.
- When asked about time, date, or "what time is it", "what date is it", "what day is it", provide the current date and time information from above.
- Remember and reference previous conversation topics when relevant to show continuity and memory.
- If asked about something you don't know, admit it honestly but offer to help find related information.
- Keep responses conversational, engaging, and informative while maintaining a professional tone.

Guidelines:
- Be friendly, approachable, and professional.
- Use emojis sparingly and appropriately (😊, 🎓, 📚, etc.) when suitable.
- Vary your response style — sometimes be more formal, sometimes more casual, depending on the question.
- Show genuine interest in helping and engaging with the user.
- Maintain a professional and helpful demeanor."""

        # Build conversation history for Gemini's chat API
        chat_history_for_gemini = []
        if chat_history:
            # Convert session history to Gemini's format (last 20 messages for better context)
            recent_history = chat_history[-20:] if len(chat_history) > 20 else chat_history
            for msg in recent_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    chat_history_for_gemini.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    chat_history_for_gemini.append({"role": "model", "parts": [content]})

        # Verify model is initialized before using it
        if model is None:
            return jsonify({"reply": "⚠️ Error: Model initialization failed. Please check the console for details."})

        # Start a chat session with history for better memory
        # Add retry logic for rate limits
        # Start a chat session with history for better memory
        # Add retry logic for rate limits
        max_retries = 3
        retry_delay = 2  # seconds
        response = None
        
        for attempt in range(max_retries):
            try:
                if chat_history_for_gemini:
                    chat = model.start_chat(history=chat_history_for_gemini)
                    # Combine system instruction with user message for better context
                    full_message = f"{system_instruction}\n\nUser's current message: {user_message}\n\nProvide a helpful, intelligent, and engaging response:"
                    response = chat.send_message(
                        full_message,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,  # Balanced temperature for intelligent and professional responses
                            top_p=0.95,
                            top_k=40,
                        )
                    )
                else:
                    # First message - no history yet
                    response = model.generate_content(
                        f"{system_instruction}\n\nUser's current message: {user_message}\n\nProvide a helpful, intelligent, and engaging response:",
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            top_p=0.95,
                            top_k=40,
                        )
                    )
                # Success - break out of retry loop
                break
            except (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests) as rate_error:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️ Rate limit hit. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    # Last attempt failed
                    raise
            except Exception as api_error:
                error_msg = str(api_error)
                print(f"⚠️ API Call Error: {error_msg}")
                print(f"Error type: {type(api_error).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                # Re-raise to be caught by outer exception handler
                raise
        # Prefer response.text when available; otherwise attempt to read from candidates
        bot_reply = getattr(response, "text", None)
        if not bot_reply:
            try:
                first_candidate = response.candidates[0]
                # Some SDK versions return parts list; join text parts if present
                parts = getattr(first_candidate, "content", None)
                if parts and hasattr(parts, "parts"):
                    text_parts = [getattr(p, "text", "") for p in parts.parts]
                    bot_reply = "".join(text_parts).strip() or None
            except Exception:
                bot_reply = None
        if not bot_reply:
            print("⚠️ Warning: Empty response from Gemini API")
            bot_reply = "⚠️ Sorry, I'm facing a technical issue connecting to Gemini AI. Please try again."

    except Exception as e:
        # Log the actual error for debugging
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"⚠️ Gemini API Error: {error_msg}")
        print(f"Error type: {error_type}")
        
        # Check for specific Google API exceptions
        is_quota_error = (
            isinstance(e, (google_exceptions.ResourceExhausted, google_exceptions.TooManyRequests)) or
            "quota" in error_msg.lower() or 
            "rate limit" in error_msg.lower() or
            "resource exhausted" in error_msg.lower() or
            "429" in error_msg
        )
        
        # Provide more specific error messages based on error type
        if "API_KEY" in error_msg or "api key" in error_msg.lower() or isinstance(e, google_exceptions.Unauthenticated):
            bot_reply = "⚠️ Error: Invalid or missing Gemini API key. Set GEMINI_API_KEY in Render Dashboard → Environment and redeploy."
        elif is_quota_error:
            bot_reply = "⚠️ Error: API quota exceeded or rate limit reached. Please wait a few moments and try again. If this persists, you may need to upgrade your API plan or wait for your quota to reset."
        elif "model" in error_msg.lower() or isinstance(e, google_exceptions.NotFound):
            bot_reply = "⚠️ Error: Model not available. Please check your API access."
        elif isinstance(e, google_exceptions.PermissionDenied):
            bot_reply = "⚠️ Error: Permission denied. Please check your API key permissions."
        else:
            bot_reply = f"⚠️ Sorry, I'm facing a technical issue: {error_msg[:100]}. Please try again."

    # Save chat history
    chat_history = session.get("chat_history", [])
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": bot_reply})
    session["chat_history"] = chat_history

    return jsonify({"reply": bot_reply})

# ----------------------
# Test Endpoint for Debugging
# ----------------------
@app.route("/test-gemini", methods=["GET"])
def test_gemini():
    """Test endpoint to check Gemini API connection"""
    try:
        if not GEMINI_API_KEY:
            return jsonify({"error": "API key not configured", "status": "error"})
        
        # List all models
        all_models = list(genai.list_models())
        model_info = []
        for m in all_models:
            model_info.append({
                "name": m.name,
                "display_name": getattr(m, 'display_name', 'N/A'),
                "supported_methods": getattr(m, 'supported_generation_methods', [])
            })
        
        # Try to initialize a model
        test_models = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
        working_model = None
        errors = []
        
        for test_model in test_models:
            try:
                model = genai.GenerativeModel(test_model)
                # Try a simple generation
                response = model.generate_content("Hello")
                working_model = test_model
                break
            except Exception as e:
                errors.append(f"{test_model}: {str(e)}")
        
        return jsonify({
            "status": "success" if working_model else "error",
            "api_key_configured": bool(GEMINI_API_KEY),
            "total_models": len(all_models),
            "models": model_info[:10],  # First 10 models
            "working_model": working_model,
            "errors": errors
        })
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        })

# ----------------------
# Feedback System
# ----------------------
@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json()
    feedback_text = data.get("feedback", "").strip()
    if not feedback_text:
        return jsonify({"status": "error", "message": "Feedback is empty."}), 400

    with open(FEEDBACKS_FILE, "a", encoding="utf-8") as f:
        f.write(feedback_text + "\n---\n")

    return jsonify({"status": "success", "message": "Feedback received. Thank you!"}), 200


@app.route("/delete-feedback", methods=["POST"])
def delete_feedback():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    data = request.get_json()
    idx = data.get("index")
    try:
        idx = int(idx)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid index."}), 400
    if not os.path.exists(FEEDBACKS_FILE):
        return jsonify({"status": "error", "message": "No feedbacks found."}), 400
    with open(FEEDBACKS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        feedbacks = [fb.strip() for fb in content.split("---") if fb.strip()]
    if idx < 0 or idx >= len(feedbacks):
        return jsonify({"status": "error", "message": "Index out of range."}), 400
    del feedbacks[idx]
    with open(FEEDBACKS_FILE, "w", encoding="utf-8") as f:
        for fb in feedbacks:
            f.write(fb + "\n---\n")
    return jsonify({"status": "success", "message": "Feedback deleted."})

@app.route("/delete-all-feedbacks", methods=["POST"])
def delete_all_feedbacks():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401
    open(FEEDBACKS_FILE, "w", encoding="utf-8").close()  # truncate
    return jsonify({"status": "success", "message": "All feedbacks deleted."})

@app.route("/view-feedbacks")
def view_feedbacks():
    if "username" not in session:
        flash("Only logged-in users can view feedbacks.", "warning")
        return redirect(url_for("login"))
    if not os.path.exists(FEEDBACKS_FILE):
        feedbacks = []
    else:
        with open(FEEDBACKS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            feedbacks = [fb.strip() for fb in content.split("---") if fb.strip()]
    feedback_items = list(enumerate(feedbacks))
    return render_template("feedbacks.html", feedbacks=feedbacks, feedback_items=feedback_items)

# ----------------------
# Run App
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)