import streamlit as st
import sqlite3
import datetime
from PIL import Image
import base64
from streamlit_calendar import calendar

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, fullname TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, 
                  file_data BLOB, 
                  uploaded_by TEXT, 
                  upload_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, 
                  description TEXT, 
                  date TEXT, 
                  added_by TEXT)''')
    
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
                  seen BOOLEAN DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message TEXT,
                  recipient TEXT,
                  timestamp TEXT,
                  seen BOOLEAN DEFAULT 0)''')
    
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

# ==================== NOTIFICATION SYSTEM ====================
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

# ==================== LOGIN PAGE ====================
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

# ==================== NOTIFICATION BELL ====================
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

# ==================== DASHBOARD COMPONENTS ====================
def show_dashboard():
    st.title("Tech Social Shield Dashboard")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="clock" style="width:200px;height:200px;border:10px solid #333;border-radius:50%;margin:0 auto;position:relative;background:#f5f5f5;">
            <div class="hand hour" style="width:6px;height:60px;background:#333;position:absolute;left:50%;bottom:50%;transform-origin:50% 100%;margin-left:-3px;"></div>
            <div class="hand minute" style="width:4px;height:80px;background:#333;position:absolute;left:50%;bottom:50%;transform-origin:50% 100%;margin-left:-2px;"></div>
            <div class="hand second" style="width:2px;height:90px;background:red;position:absolute;left:50%;bottom:50%;transform-origin:50% 100%;margin-left:-1px;"></div>
            <div class="center" style="width:12px;height:12px;border-radius:50%;background:#333;position:absolute;left:50%;top:50%;margin-left:-6px;margin-top:-6px;"></div>
        </div>
        """, unsafe_allow_html=True)
        st.write(f"**Current Time:** {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    st.subheader("Calendar")
    calendar_events = []
    calendar_component = calendar(events=calendar_events, options={
        "headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,dayGridWeek,dayGridDay"},
        "initialView": "dayGridMonth"
    })
    
    st.markdown("---")
    logo_path = st.text_input("Enter path to company logo", "tss.jpg")
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=200)
    except:
        st.warning("Logo not found at the specified path")
    st.markdown("## Tech Social Shield")

# ==================== DOCUMENT MANAGEMENT ====================
def upload_documents():
    st.title("Upload Documents")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'txt', 'xlsx', 'pptx', 'png', 'jpg', 'jpeg'])
    if uploaded_file and st.button("Upload"):
        conn = sqlite3.connect('tss_management.db')
        c = conn.cursor()
        c.execute("INSERT INTO documents (filename, file_data, uploaded_by, upload_date) VALUES (?, ?, ?, ?)",
                 (uploaded_file.name, uploaded_file.read(), st.session_state['username'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        st.success("File uploaded successfully!")

def view_documents():
    st.title("View Documents")
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    
    # Search functionality
    search_term = st.text_input("Search documents by name")
    if search_term:
        c.execute("SELECT id, filename, uploaded_by, upload_date FROM documents WHERE filename LIKE ? ORDER BY upload_date DESC", 
                 (f"%{search_term}%",))
    else:
        c.execute("SELECT id, filename, uploaded_by, upload_date FROM documents ORDER BY upload_date DESC")
    
    documents = c.fetchall()
    
    if not documents:
        st.info("No documents found")
        return
    
    for doc in documents:
        with st.expander(f"{doc[1]} (Uploaded by {doc[2]} on {doc[3]})"):
            col1, col2 = st.columns([3,1])
            
            # Download button
            with col1:
                c.execute("SELECT file_data FROM documents WHERE id=?", (doc[0],))
                file_data = c.fetchone()[0]
                st.download_button(
                    label="Download",
                    data=file_data,
                    file_name=doc[1],
                    mime="application/octet-stream",
                    key=f"download_{doc[0]}"
                )
            
            # Delete button (only for uploader or admin)
            with col2:
                if st.session_state['username'] == doc[2] or st.session_state['username'] == 'kush':
                    if st.button("Delete", key=f"delete_{doc[0]}"):
                        c.execute("DELETE FROM documents WHERE id=?", (doc[0],))
                        conn.commit()
                        st.success("Document deleted successfully!")
                        st.rerun()
    
    conn.close()

# ==================== ACHIEVEMENTS ====================
def view_achievements():
    st.title("Company Achievements")
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("SELECT title, description, date, added_by FROM achievements ORDER BY date DESC")
    for ach in c.fetchall():
        with st.expander(f"{ach[0]} - {ach[2]}"):
            st.write(f"**Added by:** {ach[3]}\n\n{ach[1]}")
    conn.close()

def add_achievement():
    st.title("Add Achievement")
    with st.form("achievement_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        date = st.date_input("Date", datetime.date.today())
        if st.form_submit_button("Add") and title and description:
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("INSERT INTO achievements (title, description, date, added_by) VALUES (?, ?, ?, ?)",
                     (title, description, date.strftime("%Y-%m-%d"), st.session_state['fullname']))
            conn.commit()
            conn.close()
            st.success("Achievement added successfully!")

# ==================== PURCHASE MANAGEMENT ====================
def purchase_request():
    st.title("Purchase Request Form")
    with st.form("purchase_form"):
        col1, col2 = st.columns(2)
        with col1:
            sr_no = st.number_input("Sr. No.", min_value=1)
            item = st.text_input("Item Name")
            price = st.number_input("Price (₹)", min_value=0.0, format="%.2f")
        with col2:
            quantity = st.number_input("Quantity", min_value=1)
            image = st.file_uploader("Upload Image", type=['jpg', 'jpeg', 'png'])
            reason = st.text_area("Reason")
        
        if st.form_submit_button("Submit") and all([sr_no, item, price, quantity, reason]):
            conn = sqlite3.connect('tss_management.db')
            c = conn.cursor()
            c.execute("""INSERT INTO purchase_requests 
                        (sr_no, item, price, image, quantity, reason, requested_by, request_date) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (sr_no, item, price, image.read() if image else None, quantity, reason, 
                      st.session_state['fullname'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            add_notification(f"New purchase request for {item} (Quantity: {quantity}) from {st.session_state['fullname']}", "kush")
            st.success("Request submitted! Kush has been notified.")

def view_purchase_requests():
    st.title("Purchase Requests")
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("""SELECT id, sr_no, item, price, quantity, reason, requested_by, request_date, status 
                 FROM purchase_requests ORDER BY request_date DESC""")
    for req in c.fetchall():
        with st.expander(f"Request #{req[0]} - {req[2]} (Status: {req[8]})"):
            cols = st.columns(2)
            cols[0].write(f"**Sr. No.:** {req[1]}\n**Item:** {req[2]}\n**Price:** ₹{req[3]:.2f}")
            cols[1].write(f"**Quantity:** {req[4]}\n**Requested by:** {req[6]}\n**Date:** {req[7]}")
            st.write(f"**Reason:** {req[5]}")
    conn.close()

def approve_purchase_requests():
    if st.session_state.get('username') != 'kush':
        st.warning("Access denied")
        return
    
    st.title("Approve Requests")
    conn = sqlite3.connect('tss_management.db')
    c = conn.cursor()
    c.execute("""SELECT id, item, quantity, requested_by FROM purchase_requests 
                 WHERE status='Pending' ORDER BY request_date""")
    
    for req in c.fetchall():
        with st.expander(f"Request #{req[0]} - {req[1]} (x{req[2]}) by {req[3]}"):
            cols = st.columns(2)
            if cols[0].button(f"Approve #{req[0]}", key=f"approve_{req[0]}"):
                c.execute("UPDATE purchase_requests SET status='Approved' WHERE id=?", (req[0],))
                conn.commit()
                st.rerun()
            if cols[1].button(f"Reject #{req[0]}", key=f"reject_{req[0]}"):
                c.execute("UPDATE purchase_requests SET status='Rejected' WHERE id=?", (req[0],))
                conn.commit()
                st.rerun()
    conn.close()

# ==================== MAIN APP ====================

      # ... (previous imports remain the same) ...

def main():
    st.set_page_config(page_title="Tech Social Shield", page_icon="🛡️", layout="wide")
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        login_page()
    else:
        st.sidebar.title(f"Welcome, {st.session_state['fullname']}")
        
        # Add logout button at the top of sidebar
        if st.sidebar.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.session_state.pop('username', None)
            st.session_state.pop('fullname', None)
            st.rerun()
        
        notification_bell()
        menu = ["Dashboard", "Upload Documents", "View Documents", "Achievements", 
                "Add Achievement", "Purchase Request", "View Purchase Requests"]
        if st.session_state.get('username') == 'kush':
            menu.append("Approve Purchase Requests")
        
        choice = st.sidebar.selectbox("Menu", menu)
        
        if choice == "Dashboard": show_dashboard()
        elif choice == "Upload Documents": upload_documents()
        elif choice == "View Documents": view_documents()
        elif choice == "Achievements": view_achievements()
        elif choice == "Add Achievement": add_achievement()
        elif choice == "Purchase Request": purchase_request()
        elif choice == "View Purchase Requests": view_purchase_requests()
        elif choice == "Approve Purchase Requests": approve_purchase_requests()

# ... (rest of the code remains identical) ...

if __name__ == "__main__":
    main()
