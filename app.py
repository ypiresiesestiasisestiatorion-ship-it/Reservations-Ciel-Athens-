import streamlit as st
import pandas as pd
from datetime import datetime

# Page Config
st.set_page_config(page_title="Διαχείριση Κρατήσεων Εστιατορίου", layout="wide", page_icon="🍽️")

# Custom CSS για καθαρή εμφάνιση & κάρτες
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: bold; color: #1F4E79; }
    .res-card {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #3B82F6;
    }
    </style>
""", unsafe_allow_html=True)

# Δημιουργία λίστας τραπεζιών & ωρών
tables_list = [f"Π{i}" for i in range(1, 31)] + ["Π60", "Π70"]
times_list = [f"{h:02d}:{m:02d}" for h in range(12, 24) for m in (0, 15, 30, 45)]

# Initialize Session State Database
if "reservations" not in st.session_state:
    st.session_state.reservations = pd.DataFrame([
        {"Ημερομηνία": pd.to_datetime("2026-08-23").date(), "Ώρα": "20:00", "Άτομα": 4, "Τραπέζι": "Π1", "Όνομα": "Γιώργος Παπαδόπουλος", "Τηλέφωνο": "6912345678", "Κατάσταση": "Επιβεβαιωμένη", "Σημειώσεις": "Κοντά στο παράθυρο"},
        {"Ημερομηνία": pd.to_datetime("2026-08-23").date(), "Ώρα": "22:00", "Άτομα": 2, "Τραπέζι": "Π5", "Όνομα": "Μαρία Ιωάννου", "Τηλέφωνο": "6923456789", "Κατάσταση": "Ήρθε ✅", "Σημειώσεις": "Γενέθλια - Τούρτα"},
        {"Ημερομηνία": pd.to_datetime("2026-08-23").date(), "Ώρα": "21:00", "Άτομα": 6, "Τραπέζι": "Π60", "Όνομα": "Κώστας Δημήτριου", "Τηλέφωνο": "6934567890", "Κατάσταση": "Επιβεβαιωμένη", "Σημειώσεις": "Παιδικό καθισματάκι"},
    ])

# Header
st.markdown("<div class='main-header'>🍽️ Βιβλίο Κρατήσεων Εστιατορίου</div>", unsafe_allow_html=True)
st.write("Διαδραστική εφαρμογή διαχείρισης σάλας & κρατήσεων")
st.divider()

# Sidebar
st.sidebar.title("🔒 Πρόσβαση Προσωπικού")
user_role = st.sidebar.selectbox("Ρόλος Χρήστη", ["Manager / Υποδοχή", "Σερβιτόρος (Προβολή μόνο)"])
selected_date = st.sidebar.date_input("Επιλογή Ημερομηνίας", datetime.strptime("2026-08-23", "%Y-%m-%d"), format="DD/MM/YYYY")

# Metrics
df = st.session_state.reservations
df_filtered = df[df["Ημερομηνία"] == selected_date].sort_values(by="Ώρα").reset_index(drop=True)

col1, col2, col3 = st.columns(3)
col1.metric("Συνολικές Κρατήσεις", len(df_filtered))
col2.metric("Σύνολο Ατόμων", int(df_filtered["Άτομα"].sum()) if not df_filtered.empty else 0)
col3.metric("Επιβεβαιωμένες", len(df_filtered[df_filtered["Κατάσταση"] == "Επιβεβαιωμένη"]))

st.divider()

# Main Tabs
tab1, tab2 = st.tabs(["📋 Κρατήσεις Ημέρας", "➕ Νέα Κράτηση"])

with tab1:
    st.subheader(f"Πρόγραμμα για {selected_date.strftime('%d/%m/%Y')}")
    
    if df_filtered.empty:
        st.info("Δεν υπάρχουν καταχωρημένες κρατήσεις για αυτή την ημερομηνία.")
    else:
        # Κεφαλίδες Λίστας
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([1, 1, 3, 2, 2, 3])
        h_col1.markdown("**Ώρα**")
        h_col2.markdown("**Τραπέζι**")
        h_col3.markdown("**Όνομα Πελάτη**")
        h_col4.markdown("**Τηλέφωνο**")
        h_col5.markdown("**Κατάσταση**")
        h_col6.markdown("**Σημειώσεις**")
        st.divider()

        # Εμφάνιση κρατήσεων χωρίς να ανοίγει πληκτρολόγιο
        for index, row in df_filtered.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 3, 2, 2, 3])
            
            # Μορφοποίηση ονόματος αν έχει έρθει/ακυρωθεί
            is_done = "Ήρθε" in row["Κατάσταση"] or "Δεν ήρθε" in row["Κατάσταση"]
            display_name = f"~~{row['Όνομα']}~~" if is_done else row["Όνομα"]
            
            c1.write(f"⏰ {row['Ώρα']}")
            c2.write(f"🪑 {row['Τραπέζι']} ({row['Άτομα']}άτ.)")
            c3.markdown(display_name)
            c4.write(row["Τηλέφωνο"])
            
            if user_role == "Manager / Υποδοχή":
                # Dropdown κουμπί που ΔΕΝ ανοίγει πληκτρολόγιο
                new_status = c5.selectbox(
                    "Κατάσταση",
                    ["Επιβεβαιωμένη", "Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"],
                    index=["Επιβεβαιωμένη", "Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"].index(row["Κατάσταση"]),
                    key=f"status_{index}",
                    label_visibility="collapsed"
                )
                
                # Ενημέρωση κατάστασης αν αλλάξει
                if new_status != row["Κατάσταση"]:
                    # Βρίσκουμε την εγγραφή στη session_state βάση και την ενημερώνουμε
                    mask = (st.session_state.reservations["Ημερομηνία"] == selected_date) & \
                           (st.session_state.reservations["Όνομα"] == row["Όνομα"]) & \
                           (st.session_state.reservations["Ώρα"] == row["Ώρα"])
                    st.session_state.reservations.loc[mask, "Κατάσταση"] = new_status
                    st.rerun()
            else:
                c5.write(row["Κατάσταση"])
                
            c6.caption(row["Σημειώσεις"])
            st.divider()

with tab2:
    if user_role == "Σερβιτόρος (Προβολή μόνο)":
        st.warning("⚠️ Δεν έχετε δικαίωμα καταχώρησης νέων κρατήσεων.")
    else:
        st.subheader("Καταχώρηση Νέας Κράτησης")
        
        with st.form("new_reservation_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            res_date = f_col1.date_input("Ημερομηνία", selected_date, format="DD/MM/YYYY")
            res_time = f_col2.selectbox("Ώρα", times_list, index=times_list.index("20:00"))
            
            f_col3, f_col4, f_col5 = st.columns(3)
            res_name = f_col3.text_input("Όνομα Πελάτη")
            res_phone = f_col4.text_input("Τηλέφωνο")
            res_guests = f_col5.number_input("Άτομα", min_value=1, max_value=30, value=2)
            
            f_col6, f_col7 = st.columns(2)
            res_table = f_col6.selectbox("Τραπέζι", tables_list)
            res_status = f_col7.selectbox("Κατάσταση", ["Επιβεβαιωμένη", "Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"])
            
            res_notes = st.text_area("Ειδικές Σημειώσεις / Προτιμήσεις")
            
            submit = st.form_submit_button("💾 Αποθήκευση Κράτησης")
            
            if submit:
                if not res_name or not res_phone:
                    st.error("Παρακαλώ συμπληρώστε Όνομα και Τηλέφωνο.")
                else:
                    new_row = {
                        "Ημερομηνία": res_date,
                        "Ώρα": res_time,
                        "Άτομα": res_guests,
                        "Τραπέζι": res_table,
                        "Όνομα": res_name,
                        "Τηλέφωνο": res_phone,
                        "Κατάσταση": res_status,
                        "Σημειώσεις": res_notes if res_notes else "-"
                    }
                    st.session_state.reservations = pd.concat([st.session_state.reservations, pd.DataFrame([new_row])], ignore_index=True)
                    st.success(f"Η κράτηση για {res_name} καταχωρήθηκε επιτυχώς!")
                    st.rerun()
