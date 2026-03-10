from flask import Flask, render_template, request, redirect, session, send_file
from db import cursor, db, execute, fetchone
from otp_service import send_otp, verify_otp
from face_utils import get_embedding, compare_embeddings
import json
from blockchain import Blockchain
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import os
import base64

app = Flask(__name__)

# Secret key from environment variable for Render
app.secret_key = os.environ.get("SECRET_KEY", "securekey")

# FIX: allow larger image uploads
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

blockchain = Blockchain()

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ---------------- HELPER FUNCTION ----------------
def get_admin_config():
    return fetchone("SELECT * FROM admin_config LIMIT 1")

#----------------main root------------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
    return render_template("admin_login.html")

# ---------------- ADMIN CONFIG ----------------
@app.route("/admin", methods=["GET","POST"])
def admin():
    if not session.get("admin"):
        return redirect("/admin_login")

    if request.method == "POST":
        execute("DELETE FROM admin_config")
        execute("""
            INSERT INTO admin_config (reg_start, reg_end, vote_start, vote_end)
            VALUES (?,?,?,?)
        """, (
            request.form["reg_start"],
            request.form["reg_end"],
            request.form["vote_start"],
            request.form["vote_end"]
        ))

    return render_template("admin.html")

# ---------------- REGISTRATION ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    config = get_admin_config()
    now = datetime.now()

    if not config or not (config["reg_start"] <= str(now) <= config["reg_end"]):
        return "Registration is currently closed"

    if request.method == "POST":

        aadhaar = request.form["aadhaar"]
        phone = request.form["phone"]

        if fetchone("SELECT * FROM registrations WHERE aadhaar=?", (aadhaar,)):
            return "Already Registered"

        user = fetchone(
            "SELECT * FROM citizens WHERE aadhaar=? AND phone=?",
            (aadhaar, phone)
        )

        if not user:
            return "Invalid Aadhaar or Phone"

        # If email not yet entered → show email box
        if "email" not in request.form:
            return render_template(
                "register.html",
                show_email=True,
                aadhaar=aadhaar,
                phone=phone
            )

        # Email entered → send OTP
        email = request.form["email"]

        send_otp(email)

        return redirect(f"/otp?aadhaar={aadhaar}&email={email}")

    return render_template("register.html")

# ---------------- OTP ----------------
@app.route("/otp", methods=["GET","POST"])
def otp():
    aadhaar = request.args.get("aadhaar")
    email = request.args.get("email")
    if request.method == "POST":
        if verify_otp(email, request.form["otp"]):
            return redirect(f"/complete_reg?aadhaar={aadhaar}")
        return "Invalid OTP"

    return render_template("otp.html")

# ---------------- COMPLETE REGISTRATION ----------------
@app.route("/complete_reg", methods=["GET","POST"])
def complete_reg():
    aadhaar = request.args.get("aadhaar")
    user = fetchone("SELECT * FROM citizens WHERE aadhaar=?", (aadhaar,))

    if request.method == "POST":
        img_data = request.form["image_data"]
        header, encoded = img_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)

        os.makedirs("faces", exist_ok=True)
        path = f"faces/{aadhaar}.png"
        with open(path, "wb") as f:
            f.write(img_bytes)

        # Create embedding
        embedding = get_embedding(path)

        execute("""
            INSERT INTO registrations (aadhaar, new_phone, face_path, face_embedding)
            VALUES (?,?,?,?)
        """, (
            aadhaar,
            request.form["new_phone"],
            path,
            json.dumps(embedding.tolist())
        ))

        return "Registration Successful"

    return render_template("complete_reg.html", user=user)

# ---------------- VOTING ----------------
@app.route("/vote", methods=["GET","POST"])
def vote():
    config = get_admin_config()
    now = datetime.now()

    if not config or not (config["vote_start"] <= str(now) <= config["vote_end"]):
        return "Voting is currently closed"

    if request.method == "POST":
        voter_id = request.form["voter_id"]
        phone = request.form["phone"]

        user = fetchone("""
            SELECT r.face_path FROM registrations r
            JOIN citizens c ON r.aadhaar = c.aadhaar
            WHERE c.voter_id=? AND r.new_phone=?
        """, (voter_id, phone))

        if not user:
            return "Verification Failed"

        # DUPLICATE VOTE CHECK
        for block in blockchain.chain:
            if isinstance(block.data, dict) and block.data["voter_id"] == voter_id:
                return "You have already voted"

        return render_template("vote_confirm.html", voter_id=voter_id)

    return render_template("vote_login.html")

# ---------------- CONFIRM VOTE ----------------
@app.route("/confirm_vote", methods=["POST"])
def confirm_vote():
    voter_id = request.form["voter_id"]
    img_data = request.form.get("image_data")

    if not img_data:
        return "Face verification required"

    header, encoded = img_data.split(",", 1)
    img_bytes = base64.b64decode(encoded)

    live_path = f"faces/live_{voter_id}.png"
    with open(live_path, "wb") as f:
        f.write(img_bytes)

    row = fetchone("""
        SELECT r.face_embedding FROM registrations r
        JOIN citizens c ON r.aadhaar=c.aadhaar
        WHERE c.voter_id=?
    """, (voter_id,))

    if not row:
        return "User not registered"

    stored_embedding = json.loads(row["face_embedding"])
    live_embedding = get_embedding(live_path)

    match = compare_embeddings(stored_embedding, live_embedding)
    if not match:
        return render_template("face_error.html")

    return render_template("vote_party.html", voter_id=voter_id)

# ---------------- FINAL VOTE ----------------
@app.route("/final_vote", methods=["POST"])
def final_vote():
    voter_id = request.form["voter_id"]
    candidate = request.form["candidate"]

    for block in blockchain.chain:
        if isinstance(block.data, dict) and block.data["voter_id"] == voter_id:
            return "You have already voted"

    blockchain.add_vote({
        "voter_id": voter_id,
        "candidate": candidate
    })

    return "Vote Stored Successfully"

# ---------------- ADMIN RESULTS ----------------
@app.route("/admin_result")
def admin_result():
    results = blockchain.count_votes()
    return render_template("admin_result.html", results=results)

# ---------------- EXPORT PDF ----------------
@app.route("/admin_result_pdf")
def admin_result_pdf():
    if not session.get("admin"):
        return "Access Denied"

    os.makedirs("reports", exist_ok=True)
    path = "reports/results.pdf"

    pdf = canvas.Canvas(path, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(200, 800, "Election Results")

    y = 750
    pdf.setFont("Helvetica", 12)
    for candidate, votes in blockchain.count_votes().items():
        pdf.drawString(200, y, f"{candidate} : {votes}")
        y -= 25

    pdf.save()
    return send_file(path, as_attachment=True)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)