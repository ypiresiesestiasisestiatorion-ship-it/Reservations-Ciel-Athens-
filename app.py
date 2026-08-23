import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# Page Config
st.set_page_config(page_title="Διαχείριση Κρατήσεων Εστιατορίου", layout="wide", page_icon="🍽️")

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 28px; font-weight: bold; color: #1F4E79; }
</style>
""", unsafe_allow_html=True)

# 1. Σύνδεση με Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 2. Σταθερές Λίστες
DAYS_GR = {
    "Monday": "Δευτέρα", "Tuesday": "Τρίτη", "Wednesday": "Τετάρτη",
    "Thursday": "Πέμπτη", "Friday": "Παρασκευή", "Saturday": "Σάββατο", "Sunday": "Κυριακή"
}

def format_date_with_day(date_obj):
    day_name = DAYS_GR[date_obj.strftime("%A")]
    return f"{day_name} {date_obj.strftime('%d/%m/%Y')}"

tables_list = [f"Π{i}" for i in range(1, 31)] + ["Π60", "Π70"]
times_list = [f"{h:02d}:{m:02d}" for h in range(12, 24) for m in (0, 15, 30, 45)]
status_options = ["Αναμονή", "Ήρθε 🟢", "Δεν ήρθε ❌"]

# 3. Τίτλος & Φίλτρο Ημερομηνίας
st.markdown('<div class="main-header">🍽️ Βιβλίο Κρατήσεων Εστιατορίου</div>', unsafe_allow_html=True)
st.caption("Διαδραστική εφαρμογή διαχείρισης σάλας & κρατήσεων (Supabase Connected)")

selected_date = st.date_input("Επιλέξτε Ημερομηνία", value=date.today())
st.write(f"### Κρατήσεις για: **{format_date_with_day(selected_date)}**")

# 4. Φόρμα Νέας Κράτησης
with st.expander("➕ Προσθήκη Νέας Κράτησης", expanded=False):
    with st.form("add_reservation_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            c_name = st.text_input("Όνομα Πελάτη *")
            c_phone = st.text_input("Τηλέφωνο", value="-")
        with col2:
            res_time = st.selectbox("Ώρα *", times_list)
            guests_num = st.number_input("Άτομα *", min_value=1, value=2)
        with col3:
            tbl_name = st.selectbox("Τραπέζι *", tables_list)
            res_notes = st.text_input("Σημειώσεις", value="-")

        submit_btn = st.form_submit_button("Αποθήκευση Κράτησης")

        if submit_btn:
            if not c_name:
                st.error("Παρακαλώ συμπληρώστε το όνομα του πελάτη!")
            else:
                new_data = {
                    "date": str(selected_date),
                    "time": str(res_time),
                    "guests": int(guests_num),
                    "table_name": str(tbl_name),
                    "customer_name": str(c_name),
                    "phone": str(c_phone),
                    "notes": str(res_notes),
                    "status": "Αναμονή"
                }
                supabase.table("reservations").insert(new_data).execute()
                st.success("Η κράτηση καταχωρήθηκε επιτυχώς!")
                st.rerun()

# 5. Ανάγνωση Δεδομένων από Supabase
response = supabase.table("reservations").select("*").eq("date", str(selected_date)).execute()
records = response.data

# 6. Προβολή Μετρικών & Πίνακα
if records:
    df = pd.DataFrame(records)
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Συνολικές Κρατήσεις", len(df))
    col_m2.metric("Σύνολο Ατόμων", df["guests"].sum())

    st.divider()
    
    # Επεξεργασία Status & Διαγραφή
    for idx, row in df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 2, 1, 2, 1])
        c1.write(f"**{row['time']}**")
        c2.write(f"**{row['table_name']}**")
        c3.write(f"{row['customer_name']} ({row['guests']} άτομα)")
        c4.write(row['phone'])
        
        # Αλλαγή Status
        current_status = row['status'] if row['status'] in status_options else "Αναμονή"
        new_status = c5.selectbox(
            "Κατάσταση",
            status_options,
            index=status_options.index(current_status),
            key=f"status_{row['id']}",
            label_visibility="collapsed"
        )
        
        if new_status != row['status']:
            supabase.table("reservations").update({"status": new_status}).eq("id", row['id']).execute()
            st.rerun()

        # Διαγραφή Κράτησης
        if c6.button("🗑️", key=f"del_{row['id']}"):
            supabase.table("reservations").delete().eq("id", row['id']).execute()
            st.rerun()
else:
    st.info("Δεν υπάρχουν κρατήσεις για την επιλεγμένη ημερομηνία.")
