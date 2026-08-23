import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="Διαχείριση Κρατήσεων Εστιατορίου", layout="wide", page_icon="🍽️")

# Custom CSS
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: bold; color: #1F4E79; }
    </style>
""", unsafe_allow_html=True)

# Λεξικό για ημέρες στα Ελληνικά
DAYS_GR = {
    "Monday": "Δευτέρα",
    "Tuesday": "Τρίτη",
    "Wednesday": "Τετάρτη",
    "Thursday": "Πέμπτη",
    "Friday": "Παρασκευή",
    "Saturday": "Σάββατο",
    "Sunday": "Κυριακή"
}

def format_date_with_day(date_obj):
    day_name = DAYS_GR[date_obj.strftime("%A")]
    return f"{day_name} {date_obj.strftime('%d/%m/%Y')}"

# Δημιουργία λίστας τραπεζιών & ωρών
tables_list = [f"Π{i}" for i in range(1, 31)] + ["Π60", "Π70"]
times_list = [f"{h:02d}:{m:02d}" for h in range(12, 24) for m in (0, 15, 30, 45)]
status_options = ["Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"]

# Initialize Selected Date in Session State
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.strptime("2026-08-23", "%Y-%m-%d").date()

# Initialize Session State Database
if "reservations" not in st.session_state:
    st.session_state.reservations = pd.DataFrame([
        {"Ημερομηνία": pd.to_datetime("2026-08-23").date(), "Ώρα": "20:00", "Άτομα": 4, "Τραπέζι": "Π1", "Όνομα": "Γιώργος Παπαδόπουλος", "Τηλέφωνο": "6912345678", "Κατάσταση": "Αναμονή", "Σημειώσεις": "Κοντά στο παράθυρο"},
        {"Ημερομηνία": pd.to_datetime("2026-08-23").date(), "Ώρα": "22:00", "Άτομα": 2, "Τραπέζι": "Π5", "Όνομα": "Μαρία Ιωάννου", "Τηλέφωνο": "6923456789", "Κατάσταση": "Ήρθε ✅", "Σημειώσεις": "Γενέθλια - Τούρτα"},
        {"Ημερομηνία": pd.to_datetime("2026-08-25").date(), "Ώρα": "20:00", "Άτομα": 4, "Τραπέζι": "Π17", "Όνομα": "Nikos", "Τηλέφωνο": "-", "Κατάσταση": "Αναμονή", "Σημειώσεις": "-"},
    ])

# Header
st.markdown("<div class='main-header'>🍽️ Βιβλίο Κρατήσεων Εστιατορίου</div>", unsafe_allow_html=True)
st.write("Διαδραστική εφαρμογή διαχείρισης σάλας & κρατήσεων")
st.divider()

# Sidebar
st.sidebar.title("🔒 Πρόσβαση Προσωπικού")
user_role = st.sidebar.selectbox("Ρόλος Χρήστη", ["Manager / Υποδοχή", "Σερβιτόρος (Προβολή μόνο)"])
st.session_state.selected_date = st.sidebar.date_input("Επιλογή Ημερομηνίας", st.session_state.selected_date, format="DD/MM/YYYY")

# Dialog για Επεξεργασία Κράτησης
@st.dialog("✏️ Επεξεργασία Κράτησης")
def edit_reservation_dialog(orig_index):
    row = st.session_state.reservations.iloc[orig_index]
    
    with st.form("edit_form"):
        e_col1, e_col2 = st.columns(2)
        e_date = e_col1.date_input("Ημερομηνία", row["Ημερομηνία"], format="DD/MM/YYYY")
        
        current_time_idx = times_list.index(row["Ώρα"]) if row["Ώρα"] in times_list else 0
        e_time = e_col2.selectbox("Ώρα", times_list, index=current_time_idx)
        
        e_col3, e_col4, e_col5 = st.columns(3)
        e_name = e_col3.text_input("Όνομα Πελάτη", str(row["Όνομα"]).replace("~~", ""))
        e_phone = e_col4.text_input("Τηλέφωνο", "" if row["Τηλέφωνο"] == "-" else row["Τηλέφωνο"])
        e_guests = e_col5.number_input("Άτομα", min_value=1, max_value=30, value=int(row["Άτομα"]))
        
        e_col6, e_col7 = st.columns(2)
        table_idx = tables_list.index(row["Τραπέζι"]) if row["Τραπέζι"] in tables_list else 0
        e_table = e_col6.selectbox("Τραπέζι", tables_list, index=table_idx)
        
        status_idx = status_options.index(row["Κατάσταση"]) if row["Κατάσταση"] in status_options else 0
        e_status = e_col7.selectbox("Κατάσταση", status_options, index=status_idx)
        
        e_notes = st.text_area("Ειδικές Σημειώσεις", "" if row["Σημειώσεις"] == "-" else row["Σημειώσεις"])
        
        save_btn = st.form_submit_button("💾 Αποθήκευση Αλλαγών")
        
        if save_btn:
            if not e_name.strip():
                st.error("Παρακαλώ συμπληρώστε το Όνομα Πελάτη.")
            else:
                st.session_state.reservations.at[orig_index, "Ημερομηνία"] = e_date
                st.session_state.reservations.at[orig_index, "Ώρα"] = e_time
                st.session_state.reservations.at[orig_index, "Άτομα"] = e_guests
                st.session_state.reservations.at[orig_index, "Τραπέζι"] = e_table
                st.session_state.reservations.at[orig_index, "Όνομα"] = e_name.strip()
                st.session_state.reservations.at[orig_index, "Τηλέφωνο"] = e_phone.strip() if e_phone.strip() else "-"
                st.session_state.reservations.at[orig_index, "Κατάσταση"] = e_status
                st.session_state.reservations.at[orig_index, "Σημειώσεις"] = e_notes.strip() if e_notes.strip() else "-"
                st.success("Η κράτηση ενημερώθηκε!")
                st.rerun()

# Metrics
df = st.session_state.reservations
df_filtered = df[df["Ημερομηνία"] == st.session_state.selected_date].sort_values(by="Ώρα")

col1, col2, col3 = st.columns(3)
col1.metric("Συνολικές Κρατήσεις", len(df_filtered))
col2.metric("Σύνολο Ατόμων", int(df_filtered["Άτομα"].sum()) if not df_filtered.empty else 0)
col3.metric("Σε Αναμονή", len(df_filtered[df_filtered["Κατάσταση"] == "Αναμονή"]))

st.divider()

# Main Tabs
tab1, tab2 = st.tabs(["📋 Κρατήσεις Ημέρας", "➕ Νέα Κράτηση"])

with tab1:
    # 📌 ΚΟΥΜΠΙΑ ΓΡΗΓΟΡΗΣ ΠΛΟΗΓΗΣΗΣ ΗΜΕΡΟΜΗΝΙΑΣ
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1.5, 1.2, 1.2, 1.2, 1.5])
    
    if nav_col1.button("◀️ Προηγούμενη"):
        st.session_state.selected_date -= timedelta(days=1)
        st.rerun()
        
    today = datetime.now().date()
    if nav_col2.button("Σήμερα"):
        st.session_state.selected_date = today
        st.rerun()
        
    if nav_col3.button("Αύριο"):
        st.session_state.selected_date = today + timedelta(days=1)
        st.rerun()
        
    if nav_col4.button("Μεθαύριο"):
        st.session_state.selected_date = today + timedelta(days=2)
        st.rerun()
        
    if nav_col5.button("Επόμενη ▶️"):
        st.session_state.selected_date += timedelta(days=1)
        st.rerun()

    # Εμφάνιση Ημέρας & Ημερομηνίας
    formatted_date = format_date_with_day(st.session_state.selected_date)
    st.subheader(f"Πρόγραμμα για {formatted_date}")
    
    if df_filtered.empty:
        st.info("Δεν υπάρχουν καταχωρημένες κρατήσεις για αυτή την ημερομηνία.")
    else:
        # Κεφαλίδες Λίστας
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6, h_col7 = st.columns([1, 1.2, 2.5, 1.8, 2, 2.5, 0.8])
        h_col1.markdown("**Ώρα**")
        h_col2.markdown("**Τραπέζι**")
        h_col3.markdown("**Όνομα Πελάτη**")
        h_col4.markdown("**Τηλέφωνο**")
        h_col5.markdown("**Κατάσταση**")
        h_col6.markdown("**Σημειώσεις**")
        h_col7.markdown("**Επεξ.**")
        st.divider()

        # Εμφάνιση κρατήσεων
        for orig_index, row in df_filtered.iterrows():
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1.2, 2.5, 1.8, 2, 2.5, 0.8])
            
            is_done = "Ήρθε" in row["Κατάσταση"] or "Δεν ήρθε" in row["Κατάσταση"]
            clean_name = str(row["Όνομα"]).replace("~~", "")
            display_name = f"~~{clean_name}~~" if is_done else clean_name
            
            c1.write(f"⏰ {row['Ώρα']}")
            c2.write(f"🪑 {row['Τραπέζι']} ({row['Άτομα']}άτ.)")
            c3.markdown(display_name)
            c4.write(row["Τηλέφωνο"])
            
            if user_role == "Manager / Υποδοχή":
                current_status = row["Κατάσταση"] if row["Κατάσταση"] in status_options else "Αναμονή"
                new_status = c5.selectbox(
                    "Κατάσταση",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"status_{orig_index}",
                    label_visibility="collapsed"
                )
                
                if new_status != row["Κατάσταση"]:
                    st.session_state.reservations.at[orig_index, "Κατάσταση"] = new_status
                    st.rerun()
                    
                if c7.button("✏️", key=f"edit_btn_{orig_index}"):
                    edit_reservation_dialog(orig_index)
            else:
                c5.write(row["Κατάσταση"])
                c7.write("-")
                
            c6.caption(row["Σημειώσεις"])
            st.divider()

with tab2:
    if user_role == "Σερβιτόρος (Προβολή μόνο)":
        st.warning("⚠️ Δεν έχετε δικαίωμα καταχώρησης νέων κρατήσεων.")
    else:
        st.subheader("Καταχώρηση Νέας Κράτησης")
        
        with st.form("new_reservation_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            res_date = f_col1.date_input("Ημερομηνία", st.session_state.selected_date, format="DD/MM/YYYY")
            res_time = f_col2.selectbox("Ώρα", times_list, index=times_list.index("20:00"))
            
            f_col3, f_col4, f_col5 = st.columns(3)
            res_name = f_col3.text_input("Όνομα Πελάτη")
            res_phone = f_col4.text_input("Τηλέφωνο (Προαιρετικό)")
            res_guests = f_col5.number_input("Άτομα", min_value=1, max_value=30, value=2)
            
            f_col6, f_col7 = st.columns(2)
            res_table = f_col6.selectbox("Τραπέζι", tables_list)
            res_status = f_col7.selectbox("Κατάσταση", status_options)
            
            res_notes = st.text_area("Ειδικές Σημειώσεις / Προτιμήσεις")
            
            submit = st.form_submit_button("💾 Αποθήκευση Κράτησης")
            
            if submit:
                if not res_name.strip():
                    st.error("Παρακαλώ συμπληρώστε το Όνομα Πελάτη.")
                else:
                    new_row = {
                        "Ημερομηνία": res_date,
                        "Ώρα": res_time,
                        "Άτομα": res_guests,
                        "Τραπέζι": res_table,
                        "Όνομα": res_name.strip(),
                        "Τηλέφωνο": res_phone.strip() if res_phone.strip() else "-",
                        "Κατάσταση": res_status,
                        "Σημειώσεις": res_notes.strip() if res_notes.strip() else "-"
                    }
                    st.session_state.reservations = pd.concat([st.session_state.reservations, pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"Η κράτηση για {res_name} καταχωρήθηκε επιτυχώς!")
                    st.rerun()
