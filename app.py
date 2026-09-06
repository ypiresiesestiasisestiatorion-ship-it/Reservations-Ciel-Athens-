import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# Page Config
st.set_page_config(page_title="Διαχείριση Κρατήσεων Εστιατορίου", layout="wide", page_icon="🍽️")

# Custom CSS
st.markdown("""
    <style>
    .main-header { font-size: 24px; font-weight: bold; color: #1F4E79; margin-bottom: 10px; }
    
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 8px 12px;
        border-radius: 8px;
    }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; color: #6c757d; }
    div[data-testid="stMetricValue"] { font-size: 18px !important; font-weight: bold; color: #1F4E79; }
    
    .big-time { font-size: 20px; font-weight: 800; color: #0d6efd; }
    .big-table { font-size: 18px; font-weight: 700; color: #212529; }
    .customer-name { font-size: 16px; font-weight: 600; color: #212529; }
    
    /* Layout Σάλας / Πλάνου */
    .floor-box {
        background-color: #eef2f5;
        border: 2px dashed #b0bec5;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .bar-label {
        background-color: #37474f;
        color: white;
        text-align: center;
        padding: 12px;
        font-weight: bold;
        border-radius: 6px;
        margin: 15px 0;
    }
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
        "date": "Ημερομηνία", "time": "Ώρα", "guests": "Άτομα",
        "table_name": "Τραπέζι", "customer_name": "Όνομα",
        "phone": "Τηλέφωνο", "status": "Κατάσταση", "notes": "Σημειώσεις"
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

TABLES_CONFIG = {
    "Ταράτσα": [f"Π{i}" for i in range(1, 31)] + ["Π60", "Π70"],
    "Εσωτερικός": [f"Κ{i}" for i in range(1, 16)] + [f"Κ{i}" for i in range(30, 34)] + ["Bar 1", "Bar 2"]
}

times_list = [f"{h:02d}:{m:02d}" for h in range(12, 24) for m in (0, 15, 30, 45)]
status_options = ["Αναμονή", "Ήρθε ✅", "Δεν ήρθε ❌"]

if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

st.session_state.reservations = fetch_all_reservations()

# Header
st.markdown("<div class='main-header'>🍽️ Βιβλίο Κρατήσεων</div>", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🔒 Πρόσβαση")
user_role = st.sidebar.selectbox("Ρόλος Χρήστη", ["Manager / Υποδοχή", "Σερβιτόρος (Προβολή μόνο)"])
st.session_state.selected_date = st.sidebar.date_input("Επιλογή Ημερομηνίας", st.session_state.selected_date, format="DD/MM/YYYY")

all_df = st.session_state.reservations.copy()
today = datetime.now().date()

sel_date = st.session_state.selected_date
df_filtered = all_df[all_df["Ημερομηνία"] == sel_date].sort_values(by="Ώρα") if not all_df.empty else pd.DataFrame()

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Κρατήσεις", len(df_filtered))
col2.metric("Άτομα", int(df_filtered["Άτομα"].sum()) if not df_filtered.empty else 0)
col3.metric("Αναμονή", len(df_filtered[df_filtered["Κατάσταση"] == "Αναμονή"]) if not df_filtered.empty else 0)

st.divider()

# --- DIALOGS ---
@st.dialog("📋 Στοιχεία Τραπεζιού")
def table_info_dialog(table_code, reservations_list):
    st.markdown(f"### Τραπέζι `{table_code}`")
    if not reservations_list:
        st.success("🟢 Το τραπέζι είναι **Ελεύθερο** για αυτή την ημερομηνία.")
    else:
        for res in reservations_list:
            with st.container(border=True):
                st.write(f"⏰ **Ώρα:** {res['Ώρα']} | 👥 **Άτομα:** {res['Άτομα']}")
                st.write(f"👤 **Όνομα:** {res['Όνομα']}")
                st.write(f"📞 **Τηλέφωνο:** {res['Τηλέφωνο']}")
                st.write(f"📌 **Status:** {res['Κατάσταση']}")
                if res['Σημειώσεις'] != "-":
                    st.caption(f"📝 {res['Σημειώσεις']}")

@st.dialog("✏️ Επεξεργασία Κράτησης")
def edit_reservation_dialog(db_id, row):
    with st.form("edit_form"):
        e_col1, e_col2 = st.columns(2)
        e_date = e_col1.date_input("Ημερομηνία", row["Ημερομηνία"], format="DD/MM/YYYY")
        current_time_idx = times_list.index(row["Ώρα"]) if row["Ώρα"] in times_list else 0
        e_time = e_col2.selectbox("Ώρα", times_list, index=current_time_idx)
        
        e_name = st.text_input("Όνομα Πελάτη", str(row["Όνομα"]).replace("~~", ""))
        e_col3, e_col4 = st.columns(2)
        e_phone = e_col3.text_input("Τηλέφωνο", "" if row["Τηλέφωνο"] == "-" else row["Τηλέφωνο"])
        e_guests = e_col4.number_input("Άτομα", min_value=1, max_value=30, value=int(row["Άτομα"]))
        
        curr_table = row["Τραπέζι"]
        curr_area = "Εσωτερικός" if curr_table in TABLES_CONFIG["Εσωτερικός"] else "Ταράτσα"
        
        e_col5, e_col6 = st.columns(2)
        e_area = e_col5.selectbox("Χώρος", ["Ταράτσα", "Εσωτερικός"], index=0 if curr_area == "Ταράτσα" else 1)
        avail_tables = TABLES_CONFIG[e_area]
        t_idx = avail_tables.index(curr_table) if curr_table in avail_tables else 0
        e_table = e_col6.selectbox("Τραπέζι", avail_tables, index=t_idx)
        
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

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Πρόγραμμα Ημέρας", "🗺️ Πλάνο Σάλας (Ταράτσα)", "➕ Νέα Κράτηση"])

def render_reservation_card(row, is_archived=False):
    db_id = row["id"]
    clean_name = str(row["Όνομα"]).replace("~~", "")
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 4, 1.5])
        with c1:
            st.markdown(f"<span class='big-time'>{row['Ώρα']}</span> &nbsp;&nbsp; | &nbsp;&nbsp; <span class='big-table'>{row['Τραπέζι']}</span> <small>({row['Άτομα']} άτ.)</small>", unsafe_allow_html=True)
            st.markdown(f"<span class='customer-name'>{clean_name}</span>", unsafe_allow_html=True)
            if row['Τηλέφωνο'] != "-":
                st.caption(f"Τηλ: {row['Τηλέφωνο']}")
        with c2:
            if row['Σημειώσεις'] != "-":
                st.write(f"📝 *{row['Σημειώσεις']}*")
            if user_role == "Manager / Υποδοχή":
                curr_st = row["Κατάσταση"] if row["Κατάσταση"] in status_options else "Αναμονή"
                new_st = st.selectbox("Status", status_options, index=status_options.index(curr_st), key=f"st_{db_id}", label_visibility="collapsed")
                if new_st != row["Κατάσταση"]:
                    supabase.table("reservations").update({"status": new_st}).eq("id", db_id).execute()
                    st.rerun()
            else:
                st.write(f"Status: **{row['Κατάσταση']}**")
        with c3:
            if user_role == "Manager / Υποδοχή":
                if st.button("✏️", key=f"btn_edit_{db_id}"):
                    edit_reservation_dialog(db_id, row)

# TAB 1: LIST VIEW
with tab1:
    n1, n2, n3, n4, n5 = st.columns(5)
    if n1.button("◀️"): st.session_state.selected_date -= timedelta(days=1); st.rerun()
    if n2.button("Σήμερα"): st.session_state.selected_date = today; st.rerun()
    if n3.button("Αύριο"): st.session_state.selected_date = today + timedelta(days=1); st.rerun()
    if n4.button("Μεθ/ριο"): st.session_state.selected_date = today + timedelta(days=2); st.rerun()
    if n5.button("▶️"): st.session_state.selected_date += timedelta(days=1); st.rerun()

    st.subheader(format_date_with_day(st.session_state.selected_date))
    
    if df_filtered.empty:
        st.info("Δεν υπάρχουν κρατήσεις για αυτή την ημερομηνία.")
    else:
        active_reservations = df_filtered[df_filtered["Κατάσταση"] != "Ήρθε ✅"]
        completed_reservations = df_filtered[df_filtered["Κατάσταση"] == "Ήρθε ✅"]
        
        subtab_active, subtab_done = st.tabs([f"⏳ Ενεργές ({len(active_reservations)})", f"✅ Ολοκληρωμένες / Ήρθαν ({len(completed_reservations)})"])
        
        with subtab_active:
            if active_reservations.empty:
                st.success("Όλες οι κρατήσεις έχουν ολοκληρωθεί!")
            else:
                for _, row in active_reservations.iterrows():
                    render_reservation_card(row, is_archived=False)
                    
        with subtab_done:
            if completed_reservations.empty:
                st.info("Δεν υπάρχουν ολοκληρωμένες κρατήσεις ακόμη.")
            else:
                for _, row in completed_reservations.iterrows():
                    render_reservation_card(row, is_archived=True)

# TAB 2: FLOOR PLAN (ΤΑΡΑΤΣΑ BASS-RELIEF BASED ON DRAWING)
with tab2:
    st.subheader(f"📍 Κάτοψη Ταράτσας - {format_date_with_day(st.session_state.selected_date)}")
    st.caption("🟢 Ελεύθερο | 🔴 Κρατημένο | 🔵 Ήρθε | Πατήστε πάνω στο τραπέζι για λεπτομέρειες")

    # Χάρτης Κρατήσεων ανά Τραπέζι
    table_status = {}
    table_res_data = {}
    
    for t in TABLES_CONFIG["Ταράτσα"]:
        t_res = df_filtered[df_filtered["Τραπέζι"] == t]
        if t_res.empty:
            table_status[t] = "🟢"
            table_res_data[t] = []
        else:
            statuses = t_res["Κατάσταση"].tolist()
            if "Ήρθε ✅" in statuses:
                table_status[t] = "🔵"
            else:
                table_status[t] = "🔴"
            table_res_data[t] = t_res.to_dict('records')

    def draw_table_btn(t_code):
        label = f"{table_status.get(t_code, '🟢')} {t_code}"
        if st.button(label, key=f"fp_{t_code}", use_container_width=True):
            table_info_dialog(t_code, table_res_data.get(t_code, []))

    st.markdown("<div class='floor-box'>", unsafe_allow_html=True)
    
    # --- 1. ΠΑΝΩ ΜΕΡΟΣ & ΑΡΙΣΤΕΡΗ/ΔΕΞΙΑ ΠΛΕΥΡΑ ---
    top_col1, top_col2, top_col3 = st.columns([1.5, 6, 1.5])
    
    with top_col1: # Αριστερός Τοίχος
        st.markdown("**Αριστερά**")
        draw_table_btn("Π1")
        draw_table_btn("Π2")
        draw_table_btn("Π3")
        draw_table_btn("Π4")

    with top_col2: # Πάνω Σειρά (Κεντρικά)
        st.markdown("**Πάνω Σειρά**")
        t_cols = st.columns(7)
        top_tables = ["Π5", "Π6", "Π7", "Π8", "Π9", "Π10", "Π11"]
        for idx, t_code in enumerate(top_tables):
            with t_cols[idx]:
                draw_table_btn(t_code)
                
        # --- ΚΕΝΤΡΙΚΟ BAR / CENTER ISLAND ---
        st.markdown("<div class='bar-label'>🍹 ΚΕΝΤΡΙΚΟ BAR / ISLAND</div>", unsafe_allow_html=True)

    with top_col3: # Δεξιά Σειρά
        st.markdown("**Δεξιά**")
        draw_table_btn("Π12")
        draw_table_btn("Π13")
        draw_table_btn("Π14")
        draw_table_btn("Π15")
        draw_table_btn("Π16")

    # --- 2. ΚΑΤΩ ΣΕΙΡΑ (ΠΛΕΥΡΑ ΘΕΑΣ / PERIMETER) ---
    st.markdown("**Κάτω Σειρά (Περίμετρος)**")
    bot_cols = st.columns(9)
    bot_tables = ["Π17", "Π18", "Π19", "Π20", "Π21", "Π22", "Π23", "Π60", "Π70"]
    for idx, t_code in enumerate(bot_tables):
        with bot_cols[idx]:
            draw_table_btn(t_code)

    st.markdown("</div>", unsafe_allow_html=True)

# TAB 3: NEW RESERVATION
with tab3:
    if user_role == "Σερβιτόρος (Προβολή μόνο)":
        st.warning("⚠️ Δεν έχετε δικαίωμα καταχώρησης.")
    else:
        st.subheader("Καταχώρηση Νέας Κράτησης")
        with st.form("new_reservation_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            res_date = f_col1.date_input("Ημερομηνία", st.session_state.selected_date, format="DD/MM/YYYY")
            res_time = f_col2.selectbox("Ώρα", times_list, index=times_list.index("20:00"))
            
            f_col3, f_col4, f_col5 = st.columns(3)
            res_name = f_col3.text_input("Όνομα Πελάτη *")
            res_phone = f_col4.text_input("Τηλέφωνο")
            res_guests = f_col5.number_input("Άτομα", min_value=1, max_value=30, value=2)
            
            f_col6, f_col7 = st.columns(2)
            selected_area = f_col6.selectbox("Χώρος", ["Ταράτσα", "Εσωτερικός"])
            res_table = f_col7.selectbox("Τραπέζι", TABLES_CONFIG[selected_area])
            
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
                    st.success("Καταχωρήθηκε επιτυχώς!")
                    st.rerun()
