import streamlit as st
import pandas as pd
import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from PIL import Image
import base64
from streamlit_calendar import calendar
import sqlite3

# Database setup
def init_db():
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, fullname TEXT)''')
    
    # Create documents table
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, 
                  file_data BLOB, 
                  uploaded_by TEXT, 
                  upload_date TEXT)''')
    
    # Create achievements table
    c.execute('''CREATE TABLE IF NOT EXISTS achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, 
                  description TEXT, 
                  date TEXT, 
                  added_by TEXT)''')
    
    # Create purchase_requests table
    c.execute('''CREATE TABLE IF NOT EXISTS purchase_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sr_no INTEGER,
                  item TEXT,
                  price REAL,
                  image BLOB,
                  quantity INTEGER,
                  reason TEXT,
                  requested_by TEXT,
                  request_date TEXT,
                  status TEXT DEFAULT 'Pending')''')
    
    # Insert default users if not exists
    users = [
        ('jaydev', 'zala', 'Jaydev Zala'),
        ('kush', 'jani', 'Kush Jani'),
        ('krishna', 'panchal', 'Krishna Panchal'),
        ('pratik', 'rohit', 'Pratik Rohit'),
        ('dhruv', 'barad', 'Dhruv Barad')
    ]
    
    for user in users:
        try:
            c.execute("INSERT INTO users VALUES (?, ?, ?)", user)
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()

init_db()

# Email configuration
def send_email(subject, body):
    sender_email = "your_smtp_email@gmail.com"  # Replace with your SMTP email
    sender_password = "your_smtp_password"      # Replace with your SMTP password
    receiver_email = "jaydevzala07@gmail.com"
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "plain"))
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# Login page
def login_page():
    st.title("Tech Social Shield Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            conn.close()
            
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user[0]
                st.session_state['fullname'] = user[2]
                st.rerun()
            else:
                st.error("Invalid username or password")

# Dashboard
def dashboard():
    st.sidebar.title(f"Welcome, {st.session_state['fullname']}")
    menu_options = ["Dashboard", "Upload Documents", "View Documents", 
                    "Achievements", "Add Achievement", 
                    "Purchase Request", "View Purchase Requests"]
    
    if st.session_state['username'] == 'kush':
        menu_options.append("Approve Purchase Requests")
    
    choice = st.sidebar.selectbox("Menu", menu_options)
    
    if choice == "Dashboard":
        show_dashboard()
    elif choice == "Upload Documents":
        upload_documents()
    elif choice == "View Documents":
        view_documents()
    elif choice == "Achievements":
        view_achievements()
    elif choice == "Add Achievement":
        add_achievement()
    elif choice == "Purchase Request":
        purchase_request()
    elif choice == "View Purchase Requests":
        view_purchase_requests()
    elif choice == "Approve Purchase Requests":
        approve_purchase_requests()

# Analog clock
def analog_clock():
    st.markdown("""
    <style>
    .clock {
        width: 200px;
        height: 200px;
        border: 10px solid #333;
        border-radius: 50%;
        margin: 0 auto;
        position: relative;
        background-color: #f5f5f5;
    }
    .hand {
        position: absolute;
        left: 50%;
        bottom: 50%;
        transform-origin: 50% 100%;
        background-color: #333;
    }
    .hour {
        width: 6px;
        height: 60px;
        margin-left: -3px;
    }
    .minute {
        width: 4px;
        height: 80px;
        margin-left: -2px;
    }
    .second {
        width: 2px;
        height: 90px;
        margin-left: -1px;
        background-color: red;
    }
    .center {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #333;
        position: absolute;
        left: 50%;
        top: 50%;
        margin-left: -6px;
        margin-top: -6px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    now = datetime.datetime.now()
    hour_angle = (now.hour % 12) * 30 + now.minute * 0.5
    minute_angle = now.minute * 6
    second_angle = now.second * 6
    
    st.markdown(f"""
    <div class="clock">
        <div class="hand hour" style="transform: rotate({hour_angle}deg);"></div>
        <div class="hand minute" style="transform: rotate({minute_angle}deg);"></div>
        <div class="hand second" style="transform: rotate({second_angle}deg);"></div>
        <div class="center"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write(f"**Current Time:** {now.strftime('%H:%M:%S')}")

# Show dashboard
def show_dashboard():
    st.title("Tech Social Shield Dashboard")
    
    # Display clock
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analog_clock()
    
    # Display calendar
    st.subheader("Calendar")
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,dayGridWeek,dayGridDay",
        },
        "initialView": "dayGridMonth",
        "initialDate": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    
    calendar_events = []
    calendar_component = calendar(events=calendar_events, options=calendar_options)
    
    # Company logo at bottom
    st.markdown("---")
    logo_path = st.text_input("Enter path to company logo", "tss.jpg")
    
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=200)
    except:
        st.warning("Logo not found at the specified path")
    
    st.markdown("## Tech Social Shield")

# Document management
def upload_documents():
    st.title("Upload Documents")
    
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'txt', 'xlsx', 'pptx'])
    
    if uploaded_file is not None:
        if st.button("Upload"):
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            
            file_data = uploaded_file.read()
            c.execute("INSERT INTO documents (filename, file_data, uploaded_by, upload_date) VALUES (?, ?, ?, ?)",
                      (uploaded_file.name, file_data, st.session_state['username'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
            st.success("File uploaded successfully!")

def view_documents():
    st.title("View Documents")
    
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("SELECT id, filename, uploaded_by, upload_date FROM documents ORDER BY upload_date DESC")
    documents = c.fetchall()
    conn.close()
    
    if not documents:
        st.info("No documents available")
        return
    
    for doc in documents:
        with st.expander(f"{doc[1]} (Uploaded by {doc[2]} on {doc[3]})"):
            st.write(f"Document ID: {doc[0]}")
            
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("SELECT file_data FROM documents WHERE id=?", (doc[0],))
            file_data = c.fetchone()[0]
            conn.close()
            
            st.download_button(
                label="Download",
                data=file_data,
                file_name=doc[1],
                mime="application/octet-stream"
            )

# Achievements
def view_achievements():
    st.title("Company Achievements")
    
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("SELECT id, title, description, date, added_by FROM achievements ORDER BY date DESC")
    achievements = c.fetchall()
    conn.close()
    
    if not achievements:
        st.info("No achievements added yet")
        return
    
    for ach in achievements:
        with st.expander(f"{ach[1]} - {ach[3]}"):
            st.write(f"**Added by:** {ach[4]}")
            st.write(ach[2])

def add_achievement():
    st.title("Add Achievement")
    
    with st.form("achievement_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        date = st.date_input("Date", datetime.date.today())
        submit_button = st.form_submit_button("Add Achievement")
        
        if submit_button and title and description:
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("INSERT INTO achievements (title, description, date, added_by) VALUES (?, ?, ?, ?)",
                      (title, description, date.strftime("%Y-%m-%d"), st.session_state['fullname']))
            conn.commit()
            conn.close()
            st.success("Achievement added successfully!")

# Purchase management
def purchase_request():
    st.title("Purchase Request Form")
    
    with st.form("purchase_form"):
        st.write("Fill the purchase request details:")
        
        col1, col2 = st.columns(2)
        with col1:
            sr_no = st.number_input("Sr. No.", min_value=1, step=1)
            item = st.text_input("Item Name")
            price = st.number_input("Price (₹)", min_value=0.0, format="%.2f")
        with col2:
            quantity = st.number_input("Quantity", min_value=1, step=1)
            image = st.file_uploader("Upload Image", type=['jpg', 'jpeg', 'png'])
            reason = st.text_area("Reason for Purchase")
        
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            if not all([sr_no, item, price, quantity, reason]):
                st.error("Please fill all required fields")
                return
            
            image_data = None
            if image is not None:
                image_data = image.read()
            
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("""INSERT INTO purchase_requests 
                         (sr_no, item, price, image, quantity, reason, requested_by, request_date) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (sr_no, item, price, image_data, quantity, reason, 
                       st.session_state['fullname'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            
            # Send email notification
            email_subject = f"New Purchase Request from {st.session_state['fullname']}"
            email_body = f"""
            A new purchase request has been submitted:
            
            Item: {item}
            Quantity: {quantity}
            Price: ₹{price:.2f}
            Reason: {reason}
            
            Please review and approve the request.
            """
            
            if send_email(email_subject, email_body):
                st.success("Request submitted successfully! Notification email sent.")
            else:
                st.success("Request submitted successfully! (Email notification failed)")

def view_purchase_requests():
    st.title("Purchase Requests")
    
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("""SELECT id, sr_no, item, price, quantity, reason, requested_by, request_date, status 
                 FROM purchase_requests 
                 ORDER BY request_date DESC""")
    requests = c.fetchall()
    conn.close()
    
    if not requests:
        st.info("No purchase requests available")
        return
    
    for req in requests:
        with st.expander(f"Request #{req[0]} - {req[2]} (Status: {req[8]})"):
            st.write(f"**Sr. No.:** {req[1]}")
            st.write(f"**Item:** {req[2]}")
            st.write(f"**Price:** ₹{req[3]:.2f}")
            st.write(f"**Quantity:** {req[4]}")
            st.write(f"**Reason:** {req[5]}")
            st.write(f"**Requested by:** {req[6]}")
            st.write(f"**Date:** {req[7]}")
            
            # Display image if available
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("SELECT image FROM purchase_requests WHERE id=?", (req[0],))
            image_data = c.fetchone()[0]
            conn.close()
            
            if image_data:
                st.image(image_data, caption=f"Image for {req[2]}", width=200)

def approve_purchase_requests():
    if st.session_state['username'] != 'kush':
        st.warning("You don't have permission to access this page")
        return
    
    st.title("Approve Purchase Requests")
    
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("""SELECT id, sr_no, item, price, quantity, reason, requested_by, request_date 
                 FROM purchase_requests 
                 WHERE status='Pending' 
                 ORDER BY request_date""")
    pending_requests = c.fetchall()
    conn.close()
    
    if not pending_requests:
        st.info("No pending purchase requests")
        return
    
    for req in pending_requests:
        with st.expander(f"Pending Request #{req[0]} - {req[2]}"):
            st.write(f"**Sr. No.:** {req[1]}")
            st.write(f"**Item:** {req[2]}")
            st.write(f"**Price:** ₹{req[3]:.2f}")
            st.write(f"**Quantity:** {req[4]}")
            st.write(f"**Reason:** {req[5]}")
            st.write(f"**Requested by:** {req[6]}")
            st.write(f"**Date:** {req[7]}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Approve Request #{req[0]}", key=f"approve_{req[0]}"):
                    conn = sqlite3.connect('tss_management.db')
                    c = conn.cursor()
                    c.execute("UPDATE purchase_requests SET status='Approved' WHERE id=?", (req[0],))
                    conn.commit()
                    conn.close()
                    st.success(f"Request #{req[0]} approved successfully!")
                    st.rerun()
            
            with col2:
                if st.button(f"Reject Request #{req[0]}", key=f"reject_{req[0]}"):
                    conn = sqlite3.connect('tss_management.db')
                    c = conn.cursor()
                    c.execute("UPDATE purchase_requests SET status='Rejected' WHERE id=?", (req[0],))
                    conn.commit()
                    conn.close()
                    st.success(f"Request #{req[0]} rejected!")
                    st.rerun()

# Main app
def main():
    st.set_page_config(page_title="Tech Social Shield", page_icon="🛡️", layout="wide")
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()
