import streamlit as st
import pandas as pd
from datetime import datetime

# Page Config
st.set_page_config(page_title="Διαχείριση Κρατήσεων Εστιατορίου", layout="wide", page_icon="🍽️")

# Custom Styling
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: bold; color: #1F4E79; }
    </style>
""", unsafe_allow_html=True)

# Δημιουργία λίστας τραπεζιών: Π1 έως Π30, + Π60, Π70
tables_list = [f"Π{i}" for i in range(1, 31)] + ["Π60", "Π70"]

# Δημιουργία λίστας ωρών ανά 15 λεπτά (12:00 έως 23:45)
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

# Sidebar - Login Simulation & Filters
st.sidebar.title("🔒 Πρόσβαση Προσωπικού")
user_role = st.sidebar.selectbox("Ρόλος Χρήστη", ["Manager / Υποδοχή", "Σερβιτόρος (Προβολή μόνο)"])
selected_date = st.sidebar.date_input("Επιλογή Ημερομηνίας", datetime.strptime("2026-08-23", "%Y-%m-%d"), format="DD/MM/YYYY")

# Metrics & Ταξινόμηση ανά Ώρα
df = st.session_state.reservations
df_filtered = df[df["Ημερομηνία"] == selected_date].sort_values(by="Ώρα").copy()

# Εφαρμογή διαγραφής (strikethrough) στα ονόματα αν ο πελάτης Ήρθε ή Δεν Ήρθε
def apply_strikethrough(row):
    status = row["Κατάσταση"]
    name = str(row["Όνομα"])
    if "Ήρθε" in status or "Δεν ήρθε" in status:
        # Αφαίρεση τυχόν προηγούμενης μορφοποίησης αν υπάρχει
        clean_name = name.replace("~~", "")
        return f"~~{clean_name}~~"
    else:
        return name.replace("~~", "")

if not df_filtered.empty:
    df_filtered["Όνομα"] = df_filtered.apply(apply_strikethrough, axis=1)

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
        status_options = ["Επιβεβαιωμένη", "Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"]
        
        if user_role == "Manager / Υποδοχή":
            st.caption("💡 Πατήστε πάνω σε οποιοδήποτε κελί για αλλαγή.")
            edited_df = st.data_editor(
                df_filtered,
                column_config={
                    "Ημερομηνία": st.column_config.DateColumn("Ημερομηνία", format="DD/MM/YYYY", required=True),
                    "Ώρα": st.column_config.SelectboxColumn("Ώρα", options=times_list, required=True),
                    "Τραπέζι": st.column_config.SelectboxColumn("Τραπέζι", options=tables_list, required=True),
                    "Κατάσταση": st.column_config.SelectboxColumn("Κατάσταση", options=status_options, required=True),
                },
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor"
            )
            
            # Ενημέρωση βάσης σε περίπτωση αλλαγής
            if not edited_df.equals(df_filtered):
                # Καθαρισμός των strikethrough από το όνομα πριν την αποθήκευση στη βάση
                edited_df["Όνομα"] = edited_df["Όνομα"].astype(str).str.replace("~~", "")
                st.session_state.reservations.update(edited_df)
                st.rerun()
        else:
            st.dataframe(
                df_filtered[["Ώρα", "Τραπέζι", "Όνομα", "Άτομα", "Τηλέφωνο", "Κατάσταση", "Σημειώσεις"]],
                use_container_width=True,
                hide_index=True
            )

with tab2:
    if user_role == "Σερβιτόρος (Προβολή μόνο)":
        st.warning("⚠️ Δεν έχετε δικαίωμα καταχώρησης νέων κρατήσεων.")
    else:
        st.subheader("Καταχώρηση Νέας Κράτησης")
        
        # Καθαρισμός πεδίων φόρμας
        def clear_form():
            st.session_state["form_name"] = ""
            st.session_state["form_phone"] = ""
            st.session_state["form_notes"] = ""

        # Αρχικοποίηση session keys φόρμας αν δεν υπάρχουν
        if "form_name" not in st.session_state:
            st.session_state["form_name"] = ""
        if "form_phone" not in st.session_state:
            st.session_state["form_phone"] = ""
        if "form_notes" not in st.session_state:
            st.session_state["form_notes"] = ""

        with st.form("new_reservation_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            res_date = f_col1.date_input("Ημερομηνία", selected_date, format="DD/MM/YYYY")
            res_time = f_col2.selectbox("Ώρα", times_list, index=times_list.index("20:00"))
            
            f_col3, f_col4, f_col5 = st.columns(3)
            res_name = f_col3.text_input("Όνομα Πελάτη", key="form_name")
            res_phone = f_col4.text_input("Τηλέφωνο", key="form_phone")
            res_guests = f_col5.number_input("Άτομα", min_value=1, max_value=30, value=2)
            
            f_col6, f_col7 = st.columns(2)
            res_table = f_col6.selectbox("Τραπέζι", tables_list)
            res_status = f_col7.selectbox("Κατάσταση", ["Επιβεβαιωμένη", "Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"])
            
            res_notes = st.text_area("Ειδικές Σημειώσεις / Προτιμήσεις", key="form_notes")
            
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
