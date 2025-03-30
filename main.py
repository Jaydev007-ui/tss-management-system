import streamlit as st
import sqlite3
import datetime
from PIL import Image
import base64
from streamlit_calendar import calendar

# Initialize Database
def init_db():
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, fullname TEXT)''')
    
    # Documents Table
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, 
                  file_data BLOB, 
                  uploaded_by TEXT, 
                  upload_date TEXT)''')
    
    # Achievements Table
    c.execute('''CREATE TABLE IF NOT EXISTS achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, 
                  description TEXT, 
                  date TEXT, 
                  added_by TEXT)''')
    
    # Purchase Requests Table
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
                  status TEXT DEFAULT 'Pending',
                  seen BOOLEAN DEFAULT 0)''')  # New column for notifications
    
    # Notifications Table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message TEXT,
                  recipient TEXT,
                  timestamp TEXT,
                  seen BOOLEAN DEFAULT 0)''')
    
    # Default Users
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

# Notification System
def add_notification(message, recipient):
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("INSERT INTO notifications (message, recipient, timestamp) VALUES (?, ?, ?)",
              (message, recipient, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_unseen_notifications(username):
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("SELECT id, message, timestamp FROM notifications WHERE recipient=? AND seen=0 ORDER BY timestamp DESC", (username,))
    notifications = c.fetchall()
    conn.close()
    return notifications

def mark_notification_as_seen(notification_id):
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("UPDATE notifications SET seen=1 WHERE id=?", (notification_id,))
    conn.commit()
    conn.close()

# Login Page
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

# Notification Bell Icon
def notification_bell():
    if st.session_state.get('username') == 'kush':
        notifications = get_unseen_notifications('kush')
        badge = f"🔔 ({len(notifications)})" if notifications else "🔔"
        
        col1, col2 = st.columns([10, 1])
        with col2:
            if st.button(badge, key="notification_bell"):
                st.session_state['show_notifications'] = True
        
        if st.session_state.get('show_notifications'):
            with st.expander("Notifications", expanded=True):
                if notifications:
                    for note in notifications:
                        st.write(f"**{note[2]}** - {note[1]}")
                        if st.button("Mark as read", key=f"mark_{note[0]}"):
                            mark_notification_as_seen(note[0])
                            st.rerun()
                else:
                    st.write("No new notifications")
                if st.button("Close"):
                    st.session_state['show_notifications'] = False

# Dashboard
def dashboard():
    st.sidebar.title(f"Welcome, {st.session_state['fullname']}")
    notification_bell()  # Show notification bell
    
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

# Purchase Request Function (Updated)
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
            
            # Add notification for Kush instead of sending email
            message = f"New purchase request for {item} (Quantity: {quantity}) from {st.session_state['fullname']}"
            add_notification(message, "kush")
            
            st.success("Purchase request submitted successfully! Kush Jani has been notified.")

# ... (Rest of the functions remain the same as in previous code) ...

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
