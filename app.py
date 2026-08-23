import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# Page Config
st.set_page_config(page_title="Διαχείριση Κρατήσεων", layout="wide", page_icon="🍽️")

# Custom CSS για Mobile βελτιστοποίηση
st.markdown("""
    <style>
    .main-header { font-size: 24px; font-weight: bold; color: #1F4E79; text-align: center; }
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def fetch_all_reservations():
    res = supabase.table("reservations").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["id", "Ημερομηνία", "Ώρα", "Άτομα", "Τραπέζι", "Όνομα", "Τηλέφωνο", "Κατάσταση", "Σημειώσεις"])
    
    df = pd.DataFrame(res.data)
    df = df.rename(columns={
        "date": "Ημερομηνία",
        "time": "Ώρα",
        "guests": "Άτομα",
        "table_name": "Τραπέζι",
        "customer_name": "Όνομα",
        "phone": "Τηλέφωνο",
        "status": "Κατάσταση",
        "notes": "Σημειώσεις"
    })
    df["Ημερομηνία"] = pd.to_datetime(df["Ημερομηνία"]).dt.date
    return df

DAYS_GR = {
    "Monday": "Δευτέρα", "Tuesday": "Τρίτη", "Wednesday": "Τετάρτη",
    "Thursday": "Πέμπτη", "Friday": "Παρασκευή", "Saturday": "Σάββατο", "Sunday": "Κυριακή"
}

def format_date_with_day(date_obj):
    day_name = DAYS_GR[date_obj.strftime("%A")]
    return f"{day_name} {date_obj.strftime('%d/%m/%Y')}"

tables_list = [f"Π{i}" for i in range(1, 31)] + ["Π60", "Π70"]
times_list = [f"{h:02d}:{m:02d}" for h in range(12, 24) for m in (0, 15, 30, 45)]
status_options = ["Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"]

if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

st.session_state.reservations = fetch_all_reservations()

# Header
st.markdown("<div class='main-header'>🍽️ Βιβλίο Κρατήσεων</div>", unsafe_allow_html=True)
st.divider()

# --- SIDEBAR ---
st.sidebar.title("🔒 Πρόσβαση")
user_role = st.sidebar.selectbox("Ρόλος", ["Manager / Υποδοχή", "Σερβιτόρος (Προβολή μόνο)"])
st.session_state.selected_date = st.sidebar.date_input("Ημερομηνία", st.session_state.selected_date, format="DD/MM/YYYY")

st.sidebar.divider()
st.sidebar.title("📊 Στατιστικά")
stats_mode = st.sidebar.selectbox("Διάστημα", ["Τρέχων Μήνας", "Τρέχον Έτος", "Προσαρμοσμένο Εύρος"])

all_df = st.session_state.reservations.copy()
today = datetime.now().date()

if stats_mode == "Τρέχων Μήνας":
    start_d, end_d = today.replace(day=1), today
elif stats_mode == "Τρέχον Έτος":
    start_d, end_d = today.replace(month=1, day=1), today
else:
    date_range = st.sidebar.date_input("Εύρος", value=(today - timedelta(days=7), today), format="DD/MM/YYYY")
    start_d, end_d = (date_range[0], date_range[1]) if isinstance(date_range, tuple) and len(date_range) == 2 else (today, today)

filtered_stats = all_df[(all_df["Ημερομηνία"] >= start_d) & (all_df["Ημερομηνία"] <= end_d)] if not all_df.empty else pd.DataFrame()

st.sidebar.metric("Συνολικές Κρατήσεις", len(filtered_stats))
st.sidebar.metric("Σύνολο Ατόμων", int(filtered_stats["Άτομα"].sum()) if not filtered_stats.empty else 0)

# Dialog για Επεξεργασία
@st.dialog("✏️ Επεξεργασία Κράτησης")
def edit_reservation_dialog(db_id, row):
    with st.form("edit_form"):
        e_date = st.date_input("Ημερομηνία", row["Ημερομηνία"], format="DD/MM/YYYY")
        current_time_idx = times_list.index(row["Ώρα"]) if row["Ώρα"] in times_list else 0
        e_time = st.selectbox("Ώρα", times_list, index=current_time_idx)
        
        e_name = st.text_input("Όνομα Πελάτη", str(row["Όνομα"]).replace("~~", ""))
        e_phone = st.text_input("Τηλέφωνο", "" if row["Τηλέφωνο"] == "-" else row["Τηλέφωνο"])
        e_guests = st.number_input("Άτομα", min_value=1, max_value=30, value=int(row["Άτομα"]))
        
        table_idx = tables_list.index(row["Τραπέζι"]) if row["Τραπέζι"] in tables_list else 0
        e_table = st.selectbox("Τραπέζι", tables_list, index=table_idx)
        
        status_idx = status_options.index(row["Κατάσταση"]) if row["Κατάσταση"] in status_options else 0
        e_status = st.selectbox("Κατάσταση", status_options, index=status_idx)
        e_notes = st.text_area("Σημειώσεις", "" if row["Σημειώσεις"] == "-" else row["Σημειώσεις"])
        
        if st.form_submit_button("💾 Αποθήκευση"):
            if e_name.strip():
                updated_data = {
                    "date": str(e_date), "time": str(e_time), "guests": int(e_guests),
                    "table_name": str(e_table), "customer_name": e_name.strip(),
                    "phone": e_phone.strip() if e_phone.strip() else "-",
                    "status": str(e_status), "notes": e_notes.strip() if e_notes.strip() else "-"
                }
                supabase.table("reservations").update(updated_data).eq("id", db_id).execute()
                st.success("Ενημερώθηκε!")
                st.rerun()

# Metrics Κεντρικής Οθόνης
sel_date = st.session_state.selected_date
df_filtered = all_df[all_df["Ημερομηνία"] == sel_date].sort_values(by="Ώρα") if not all_df.empty else pd.DataFrame()

col1, col2, col3 = st.columns(3)
col1.metric("Κρατήσεις", len(df_filtered))
col2.metric("Άτομα", int(df_filtered["Άτομα"].sum()) if not df_filtered.empty else 0)
col3.metric("Αναμονή", len(df_filtered[df_filtered["Κατάσταση"] == "Αναμονή"]) if not df_filtered.empty else 0)

st.divider()

# Main Tabs
tab1, tab2 = st.tabs(["📋 Κρατήσεις", "➕ Νέα Κράτηση"])

with tab1:
    # Πλοήγηση Ημερομηνιών
    n1, n2, n3, n4, n5 = st.columns(5)
    if n1.button("◀️"): st.session_state.selected_date -= timedelta(days=1); st.rerun()
    if n2.button("Σήμερα"): st.session_state.selected_date = today; st.rerun()
    if n3.button("Αύριο"): st.session_state.selected_date = today + timedelta(days=1); st.rerun()
    if n4.button("Μεθ/ριο"): st.session_state.selected_date = today + timedelta(days=2); st.rerun()
    if n5.button("▶️"): st.session_state.selected_date += timedelta(days=1); st.rerun()

    st.subheader(format_date_with_day(st.session_state.selected_date))
    
    if df_filtered.empty:
        st.info("Καμία κράτηση για αυτή την ημερομηνία.")
    else:
        # MOBILE-FRIENDLY ΚΑΡΤΕΣ ΚΡΑΤΗΣΕΩΝ
        for idx, row in df_filtered.iterrows():
            db_id = row["id"]
            is_done = "Ήρθε" in str(row["Κατάσταση"]) or "Δεν ήρθε" in str(row["Κατάσταση"])
            clean_name = str(row["Όνομα"]).replace("~~", "")
            display_name = f"~~{clean_name}~~" if is_done else clean_name
            
            # Κάθε κράτηση σε δικό της αυτόνομο πλαίσιο (Card)
            with st.container(border=True):
                # Γραμμή 1: Ώρα, Τραπέζι & Κουμπί Επεξεργασίας
                top_col1, top_col2 = st.columns([4, 1])
                with top_col1:
                    st.markdown(f"⏰ **{row['Ώρα']}** | 🪑 **{row['Τραπέζι']}** ({row['Άτομα']} άτομα)")
                with top_col2:
                    if user_role == "Manager / Υποδοχή":
                        if st.button("✏️", key=f"edit_{db_id}"):
                            edit_reservation_dialog(db_id, row)

                # Γραμμή 2: Όνομα & Τηλέφωνο
                st.markdown(f"👤 **{display_name}** — 📞 `{row['Τηλέφωνο']}`")
                
                # Γραμμή 3: Σημειώσεις
                if row['Σημειώσεις'] != "-":
                    st.caption(f"📝 {row['Σημειώσεις']}")

                # Γραμμή 4: Κατάσταση
                if user_role == "Manager / Υποδοχή":
                    current_status = row["Κατάσταση"] if row["Κατάσταση"] in status_options else "Αναμονή"
                    new_status = st.selectbox(
                        "Κατάσταση",
                        status_options,
                        index=status_options.index(current_status),
                        key=f"status_{db_id}",
                        label_visibility="collapsed"
                    )
                    if new_status != row["Κατάσταση"]:
                        supabase.table("reservations").update({"status": new_status}).eq("id", db_id).execute()
                        st.rerun()
                else:
                    st.write(f"Status: **{row['Κατάσταση']}**")

with tab2:
    if user_role == "Σερβιτόρος (Προβολή μόνο)":
        st.warning("⚠️ Δεν έχετε δικαίωμα καταχώρησης.")
    else:
        st.subheader("Νέα Κράτηση")
        with st.form("new_reservation_form", clear_on_submit=True):
            res_date = st.date_input("Ημερομηνία", st.session_state.selected_date, format="DD/MM/YYYY")
            res_time = st.selectbox("Ώρα", times_list, index=times_list.index("20:00"))
            res_name = st.text_input("Όνομα Πελάτη *")
            res_phone = st.text_input("Τηλέφωνο")
            res_guests = st.number_input("Άτομα", min_value=1, max_value=30, value=2)
            res_table = st.selectbox("Τραπέζι", tables_list)
            res_status = st.selectbox("Κατάσταση", status_options)
            res_notes = st.text_area("Σημειώσεις")
            
            if st.form_submit_button("💾 Αποθήκευση"):
                if not res_name.strip():
                    st.error("Συμπληρώστε το Όνομα.")
                else:
                    new_db_row = {
                        "date": str(res_date), "time": str(res_time), "guests": int(res_guests),
                        "table_name": str(res_table), "customer_name": res_name.strip(),
                        "phone": res_phone.strip() if res_phone.strip() else "-",
                        "status": str(res_status), "notes": res_notes.strip() if res_notes.strip() else "-"
                    }
                    supabase.table("reservations").insert(new_db_row).execute()
                    st.success("Καταχωρήθηκε!")
                    st.rerun()
