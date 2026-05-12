"""
Email Service for sending OTP notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import os


class EmailService:
    def __init__(self):
        self.sender_email = os.getenv('SENDER_EMAIL', 'visitorchecki@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', 'jrum xlan wnld jiug')

    def send_otp_to_roommates(self, room_number, roommates, otp_code, image_path=None):
        """Send OTP to all roommates of a room"""
        success_count = 0
        failed_emails = []

        try:
            # 🔥 Create ONE connection (important fix)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)

            for roommate in roommates:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = self.sender_email
                    msg['To'] = roommate['email']
                    msg['Subject'] = f'🔔 Visitor at Room {room_number} - OTP Required'

                    body = f"""
Hello {roommate['name']},

A visitor is at your door (Room {room_number}).

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

====================
   OTP: {otp_code}
====================

Share this OTP ONLY if you know the visitor.

- Visitor Access System
                    """

                    msg.attach(MIMEText(body, 'plain'))

                    # 📸 Attach image (optional)
                    if image_path and os.path.exists(image_path):
                        try:
                            with open(image_path, 'rb') as f:
                                img = MIMEImage(f.read(), name=os.path.basename(image_path))
                                msg.attach(img)
                        except Exception:
                            pass

                    server.send_message(msg)
                    print(f"OTP sent to {roommate['email']}")
                    success_count += 1

                except Exception as e:
                    print(f"Failed: {roommate['email']}")
                    failed_emails.append(roommate['email'])

            server.quit()

        except Exception as e:
            print("Email service error:", e)

        return success_count, failed_emails

    def send_high_risk_alert(self, room_number, roommates, risk_score):
        """Send high-risk alert"""
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)

            for roommate in roommates:
                msg = MIMEMultipart()
                msg['From'] = self.sender_email
                msg['To'] = roommate['email']
                msg['Subject'] = f'⚠️ HIGH RISK ALERT - Room {room_number}'

                body = f"""
SECURITY ALERT

High-risk visitor detected at Room {room_number}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Risk Score: {risk_score}

ACCESS DENIED

- Visitor Access System
                """

                msg.attach(MIMEText(body, 'plain'))
                server.send_message(msg)

                print(f"Alert sent to {roommate['email']}")

            server.quit()

        except Exception as e:
            print("High-risk email error:", e)