import random
import smtplib
from email.mime.text import MIMEText

# store OTP temporarily
otp_store = {}

# Gmail credentials
SENDER_EMAIL = "mathewsk2003@gmail.com"
APP_PASSWORD = "xkzh evqk jjwe hfoq"


def send_otp(email):

    otp = str(random.randint(100000, 999999))

    otp_store[email] = otp

    message = MIMEText(f"Your OTP for voting registration is: {otp}")
    message["Subject"] = "Voting Registration OTP"
    message["From"] = SENDER_EMAIL
    message["To"] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(message)
        server.quit()

        print("OTP sent to email:", email)

    except Exception as e:
        print("Email sending failed:", e)


def verify_otp(email, user_otp):

    stored_otp = otp_store.get(email)

    if stored_otp and stored_otp == user_otp:
        del otp_store[email]
        return True

    return False