import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from st_aggrid.shared import GridUpdateMode, DataReturnMode
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from io import StringIO
import datetime
import re
from upload_image import upload_to_database,delete_cloudinary_image, rename_cloudinary_image
from datetime import date


v_usn = st.secrets.username.V_USN
n_usn = st.secrets.username.N_USN

if "page" not in st.session_state:
    st.session_state.page = "Login"

def reset_cache():
    # Clear semua cache
    st.cache_data.clear()
    # Clear session state
    for key in ['existing_data', 'conn', 'all_images']:
        if key in st.session_state:
            del st.session_state[key]

    
    st.session_state.page = 'Home'
    st.rerun()

st.set_page_config(layout="wide")
pad_ding = st.markdown("""
    <style>
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)  # Cache data for 10 minutes
def load_gsheet_data(username):
    conn = st.connection("gsheets", type=GSheetsConnection)
    if username == "zedkari":
        List = conn.read(worksheet="NList", usecols=list(range(14)))
    elif username == "vincent":
        List = conn.read(worksheet="VList", usecols=list(range(4)))
    return List

@ st.cache_resource
def connection():
    conn = st.connection('gsheets', type=GSheetsConnection)
    return conn

if 'conn' not in st.session_state:
    st.session_state.conn = connection()

conn = st.session_state.conn

# Cache image fetching function
@st.cache_data(ttl=600)  # Cache the image for 10 minutes as well
def fetch_image(image_url):
    try:
        # Fetch image from URL
        response = requests.get(image_url)
        return response.content
    except Exception as e:
        st.error(f"Error fetching image: {e}")
        return None
    
# Pre-fetch all images for all rows and cache them
@st.cache_data(ttl=600)
def cache_all_images(df):
    images = {}
    for _, row in df.iterrows():
        picture_url = row['Picture']
        if pd.notna(picture_url):  # Only fetch if picture URL is available
            images[row['Name (Kanji)']] = fetch_image(picture_url)
    return images

if "log_in" not in st.session_state:
    conn = st.connection("gsheets", type=GSheetsConnection)
    Login = conn.read(worksheet="Login", usecols=list(range(2)))
    st.session_state.log_in = Login

login_data = st.session_state.log_in

if 'usn' not in st.session_state:
    st.session_state.usn = 'None'

REVIEW_OPTS = [
    "Not Watched",
    "Watched",
    "Goat"
]

SIZE_OPTS = [
    "?", # No Info
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J"
]

STATUS_OPTS = [
    "Active",
    "Retired",
    "No Info",
    "Problem",
    "Slow Release"
]

INFO = [
    "Not Checked",
    "Pass",
    "Drop"
]

if st.session_state.page != "Login":
    st.sidebar.title("Menu")
    if st.sidebar.button("🔄 Refresh Data & Clear Cache"):
        reset_cache()
        
    if st.sidebar.button("Logout"):
        st.session_state.page = "Login"
        st.cache_data.clear()
        # Clear session state
        for key in ['existing_data', 'conn', 'all_images']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ===============================
# LOGIN
# ===============================
if st.session_state.page == 'Login':
    left,mid,right = st.columns([1.5,1,1.5])
    with mid:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Load data once and store it in session state
            user = login_data[login_data["Username"] == username]

            if not user.empty:
                stored_password = user["Password"].iloc[0]

                if password == stored_password:
                    st.session_state.logged_in = True
                    st.success("Login berhasil!")
                    st.session_state.page = 'Home'
                    st.session_state.usn = username
                    st.rerun()
                else:
                    st.error("❌ Password salah")
            else:
                st.error("❌ Username tidak ditemukan")

# ===============================
# HOME
# ===============================
elif st.session_state.page == 'Home':
    # Load data once and store it in session state
    conn = st.session_state.conn
    usn = st.session_state.usn
    if 'existing_data' not in st.session_state:
        st.session_state.existing_data = load_gsheet_data(usn)

    existing_data = st.session_state.existing_data

    # Cache all images
    if 'all_images' not in st.session_state:
        st.session_state.all_images = cache_all_images(existing_data)

    # =======================
    # SIDEBAR FORM INPUT
    # =======================
    
    st.sidebar.header("📋 Input Actress Data")
    # Tambahkan navigasi di sidebar
    if usn == n_usn:
        st.sidebar.title("Navigation")
        if st.sidebar.button("📋 Manage Data"):
            st.session_state.page = "Home"
            st.rerun()
        
        if st.sidebar.button("👩‍🎤 View Gallery"):
            st.session_state.page = "Gallery"
            st.rerun()

    picture = st.sidebar.file_uploader("Upload Picture", type=["jpg", "jpeg", "png"])
    if picture is not None:
        st.sidebar.image(picture, width=100)

    if usn == n_usn:
        review = st.sidebar.selectbox(
            "Review *",
            options=REVIEW_OPTS,
            index=None
        )

    name_alpha = st.sidebar.text_input("Name (Alphabet) *")

    name_kanji = st.sidebar.text_input("Name (Kanji) *")

    if usn == n_usn:
        birthdate = st.sidebar.date_input(
            "Birthdate",
            min_value=datetime.date(1950, 1, 1),
            max_value=datetime.date.today()
        )

        if st.sidebar.checkbox("No Info"):
            formatted_birthdate = "?"
        else:
            formatted_birthdate = birthdate.strftime("%d/%m/%Y")

        debut_date = st.sidebar.date_input(
            "Debut Date",
            min_value=datetime.date(1950, 1, 1),
            max_value=datetime.date.today()
        )
        if st.sidebar.checkbox("No Info "):
            formatted_debutDate = "?"
        else:
            formatted_debutDate = debut_date.strftime("%d/%m/%Y")

        size = st.sidebar.selectbox(
            "Size *",
            options=SIZE_OPTS,
            index=None
        )

        st.sidebar.write("Measurement")
        bust = st.sidebar.number_input("Bust (cm)", min_value=0, max_value=200)
        waist = st.sidebar.number_input("Waist (cm)", min_value=0, max_value=200)
        hip = st.sidebar.number_input("Hip (cm)", min_value=0, max_value=200)
        if st.sidebar.checkbox("No Info  "):
            measure = "?"
        else:
            if bust == 0 or waist == 0 or hip == 0:
                measure = "?"
            else:
                measure = f"B{bust} / W{waist} / H{hip}"

        height = st.sidebar.number_input("Height (cm)", min_value=130, max_value=300)
        if st.sidebar.checkbox("No Info   "):
            height = "?"

        notes = st.sidebar.text_area("Notes")

        status = st.sidebar.selectbox(
            "Status *",
            options=STATUS_OPTS,
            index=None
        )
        
        if status == "Retired":
            retired_date = st.sidebar.date_input(
                "Retired Date *",
                value = datetime.date.today()
            )
            formatted_retire = retired_date.strftime("%d/%m/%Y")
        else:
            formatted_retire = "-"
    
    if usn == v_usn:
        info = st.sidebar.selectbox(
            "Status *",
            options = INFO,
            index=None
        )

    submit = st.sidebar.button("💾 Save Data")

    if submit:
        if usn == n_usn:
            if not existing_data.empty:
                if not review or name_alpha == '' or name_kanji == '' or not size or height == 130 or not status:
                    st.sidebar.warning("Ensure all mandatory fields are filled.")
                elif existing_data['Name (Kanji)'].str.contains(name_kanji).any():
                    st.sidebar.warning(f"An Actress with this Kanji : {name_kanji} already exist")
                else:
                    st.sidebar.success("Data submitted successfully!")

                    if(formatted_birthdate!="?"):
                        dob = pd.to_datetime(formatted_birthdate, format=f'%d/%m/%Y')
                    
                    if(formatted_debutDate != '?'):
                        dod = pd.to_datetime(formatted_debutDate, format=f'%d/%m/%Y')
                    
                    if(formatted_retire != '-'):
                        dor = pd.to_datetime(formatted_retire, format=f'%d/%m/%Y')

                    if formatted_birthdate == "?":
                        age = "?"
                    else:
                        age = date.today().year - dob.year

                    if formatted_debutDate == "?" and status != "Retired":
                        debut = '?'
                    elif formatted_debutDate != "?" and status != "Retired":
                        period_year = date.today().year - dod.year
                        period_month = date.today().month - dod.month
                        if date.today().day < dod.day:
                            period_month -= 1

                        if period_month < 0:
                            period_year -= 1
                            period_month += 12
                        
                        if period_month == 0:
                            debut = f"{period_year} Year"
                        else:
                            debut = f"{period_year} Year {period_month} Month"
                    elif formatted_debutDate == "?" and status == "Retired":
                        debut = "?"
                    elif formatted_debutDate != "?" and status == "Retired":
                        period_year = dor.year - dod.year
                        period_month = dor.month - dod.month
                        if dor.day < dod.day:
                            period_month -= 1

                        if period_month < 0:
                            period_year -= 1
                            period_month += 12
                        
                        if period_month == 0:
                            debut = f"{period_year} Year"
                        else:
                            debut = f"{period_year} Year {period_month} Month"
                    
                    join_name = name_alpha  # ⬅️ Tambah .iloc[0]
                    clean_name = re.sub(r'[^\w]','',join_name)
                    clean_name = "N"+clean_name
                    
                    if picture is not None:
                        link = upload_to_database(picture, clean_name)
                    else:
                        link = "https://res.cloudinary.com/devooeuej/image/upload/v1763270494/Placeholder.png"

                    new_data = pd.DataFrame(
                        [
                            {
                                "Picture": link,
                                "Review": review,
                                "Name (Alphabet)" : name_alpha,
                                "Name (Kanji)": name_kanji,
                                "Birthdate": formatted_birthdate,
                                "Debut Date": formatted_debutDate,
                                "Size" : size,
                                "Measurement": measure,
                                "Height (cm)" : str(height) + ' cm',
                                "Notes" : notes,
                                "Age": age,
                                "Debut Period": debut,
                                "Retire Date": formatted_retire,
                                "Status": status,
                            }
                        ]
                    )
                    
                    new_df = pd.concat([existing_data,new_data], ignore_index=True)
                    conn.update(worksheet="NList", data=new_df)
                    reset_cache()
            else:
                st.sidebar.success("Data submitted successfully!")

                if(formatted_birthdate!="?"):
                    dob = pd.to_datetime(formatted_birthdate, format=f'%d/%m/%Y')
                
                if(formatted_debutDate != '?'):
                    dod = pd.to_datetime(formatted_debutDate, format=f'%d/%m/%Y')
                
                if(formatted_retire != '-'):
                    dor = pd.to_datetime(formatted_retire, format=f'%d/%m/%Y')

                if formatted_birthdate == "?":
                    age = "?"
                else:
                    age = date.today().year - dob.year

                if formatted_debutDate == "?" and status != "Retired":
                    debut = '?'
                elif formatted_debutDate != "?" and status != "Retired":
                    period_year = date.today().year - dod.year
                    period_month = date.today().month - dod.month
                    if date.today().day < dod.day:
                        period_month -= 1

                    if period_month < 0:
                        period_year -= 1
                        period_month += 12
                    
                    if period_month == 0:
                        debut = f"{period_year} Year"
                    else:
                        debut = f"{period_year} Year {period_month} Month"
                elif formatted_debutDate == "?" and status == "Retired":
                    debut = "?"
                elif formatted_debutDate != "?" and status == "Retired":
                    period_year = dor.year - dod.year
                    period_month = dor.month - dod.month
                    if dor.day < dod.day:
                        period_month -= 1

                    if period_month < 0:
                        period_year -= 1
                        period_month += 12
                    
                    if period_month == 0:
                        debut = f"{period_year} Year"
                    else:
                        debut = f"{period_year} Year {period_month} Month"
                
                join_name = name_alpha  # ⬅️ Tambah .iloc[0]
                clean_name = re.sub(r'[^\w]','',join_name)
                clean_name = "N"+clean_name
                
                if picture is not None:
                    link = upload_to_database(picture, clean_name)
                else:
                    link = "https://res.cloudinary.com/devooeuej/image/upload/v1763270494/Placeholder.png"

                new_data = pd.DataFrame(
                    [
                        {
                            "Picture": link,
                            "Review": review,
                            "Name (Alphabet)" : name_alpha,
                            "Name (Kanji)": name_kanji,
                            "Birthdate": formatted_birthdate,
                            "Debut Date": formatted_debutDate,
                            "Size" : size,
                            "Measurement": measure,
                            "Height (cm)" : str(height) + ' cm',
                            "Notes" : notes,
                            "Age": age,
                            "Debut Period": debut,
                            "Retire Date": formatted_retire,
                            "Status": status,
                        }
                    ]
                )
                
                new_df = pd.concat([existing_data,new_data], ignore_index=True)
                conn.update(worksheet="NList", data=new_df)
                reset_cache()
        elif usn == v_usn:
            if not existing_data.empty:
                if name_alpha == '' or not info:
                    st.sidebar.warning("Ensure all mandatory fields are filled.")
                elif existing_data['Name (Alphabet)'].str.contains(name_alpha).any():
                    st.sidebar.warning(f"An Actress with this Name : {name_alpha} already exist")
                else:
                    st.sidebar.success("Data submitted successfully!")
                    join_name = name_alpha  # ⬅️ Tambah .iloc[0]
                    clean_name = re.sub(r'[^\w]','',join_name)
                    clean_name = "V"+clean_name
                    
                    if picture is not None:
                        link = upload_to_database(picture, clean_name)
                    else:
                        link = "https://res.cloudinary.com/devooeuej/image/upload/v1763270494/Placeholder.png"

                    if name_kanji == '' or name_kanji == None:
                        name_kanji = ""
                        
                    new_data = pd.DataFrame(
                        [
                            {
                                "Picture": link,
                                "Name (Alphabet)" : name_alpha,
                                "Name (Kanji)": name_kanji,
                                "Status" : info
                            }
                        ]
                    )
                    
                    new_df = pd.concat([existing_data,new_data], ignore_index=True)
                    conn.update(worksheet="VList", data=new_df)
                    reset_cache()
            else:
                st.sidebar.success("Data submitted successfully!")
                join_name = name_alpha  # ⬅️ Tambah .iloc[0]
                clean_name = re.sub(r'[^\w]','',join_name)
                clean_name = "V"+clean_name
                
                if picture is not None:
                    link = upload_to_database(picture, clean_name)
                else:
                    st.sidebar.write('image Kosong')
                    link = "https://res.cloudinary.com/devooeuej/image/upload/v1763270494/Placeholder.png"

                if name_kanji == '' or name_kanji == None:
                    name_kanji = ""
                new_data = pd.DataFrame(
                    [
                        {
                            "Picture": link,
                            "Name (Alphabet)" : name_alpha,
                            "Name (Kanji)": name_kanji,
                            "Status" : info
                        }
                    ]
                )
                
                new_df = pd.concat([existing_data,new_data], ignore_index=True)
                conn.update(worksheet="VList", data=new_df)
                reset_cache()


    st.title("Actress List") 

    if existing_data.empty:
        st.info("No data Yet")
    else:
        col1,col2 = st.columns([1,1])
        if usn == n_usn:
            df_filter = existing_data[['Review','Name (Alphabet)','Name (Kanji)']].copy()
            df_filter.loc[:, 'Name'] = df_filter['Name (Alphabet)'] + " (" + df_filter['Name (Kanji)'] + ")"

            df_table = df_filter[['Review', 'Name']].copy()

            # Bangun konfigurasi grid
            gb = GridOptionsBuilder.from_dataframe(df_filter[['Review','Name']])

            # 🔹 Atur lebar kolom, freeze, dan alignment
            gb.configure_column("Review", header_name="Review", width=42,  cellStyle=JsCode("""
                    function(params) {
                        // text align tengah
                        let style = {'textAlign':'Center'};

                        // conditional background color
                        if(params.value === 'Goat'){
                            style.backgroundColor = '#473822';
                            style.color = 'white';
                        }
                        else if(params.value === 'Not Watched'){
                            style.backgroundColor = '#b10202';
                            style.color = 'white';
                        }
                        else{
                            style.backgroundColor = '#11734b';
                            style.color = 'white';
                        }

                        return style;
                    }
                """))
            gb.configure_column("Name", header_name="Name", width=75,  cellStyle={'textAlign': 'left'})
        elif usn == v_usn:
            gb = GridOptionsBuilder.from_dataframe(existing_data[['Name (Alphabet)', 'Name (Kanji)']])
            gb.configure_column("Name (Alphabet)", header_name="Name (Alphabet)", width=75,  cellStyle={'textAlign': 'left'})
            gb.configure_column("Name (Kanji)", header_name="Name (Kanji)", width=75,  cellStyle={'textAlign': 'left'})
            
        # Opsi tambahan
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        gb.configure_grid_options(alwaysShowHorizontalScroll=True, suppressHorizontalScroll=False, enableRangeSelection=True, pagination=True, paginationPageSize=10000, domLayout='normal')

        # Bangun grid option
        gridOptions = gb.build()

        # Tampilkan di Streamlit
        with col1:
            if usn == n_usn:
                data = df_filter
            elif usn == v_usn:
                data = existing_data

            agdf = AgGrid(
                data,
                gridOptions=gridOptions,
                height=900,
                theme="balham",
                update_mode="SELECTION_CHANGED",
                allow_unsafe_jscode=True
            )

        with col2:
            selected = agdf["selected_rows"]

            if selected is not None and len(selected) > 0:
                sub_col1, sub_col2, sub_col3 = st.columns([1,1,1])

                if usn == n_usn:
                    selected_name = selected.iloc[0]["Name (Kanji)"]
                    filtered_df = existing_data[existing_data["Name (Kanji)"] == selected_name].copy()
                elif usn == v_usn:
                    selected_name = selected.iloc[0]['Name (Alphabet)']
                    filtered_df = existing_data[existing_data["Name (Alphabet)"] == selected_name].copy()
                # Filter df_detail berdasarkan nama yang dipilih
                picture = filtered_df['Picture'].iloc[0]
                filtered_row = filtered_df.iloc[0]  # satu row
                picture_content = st.session_state.all_images.get(selected_name)
                with sub_col2:
                    if picture:
                        st.image(picture, width=150)
                    else:
                        st.write("No picture available.")

                st.subheader(f"**Description:** ")

                if usn == n_usn:
                    for col in filtered_df.columns:
                        col1, col2 = st.columns([1, 2]) # kolom 1 untuk label, kolom 2 untuk value
                        if col != "Picture" and col != "Birthdate" and col != "Debut Date" and col != "Retire Date":
                            col1.write(f"**{col}**")
                            col2.write(f"{filtered_row[col]}")
                        elif col == 'Birthdate' or col == 'Debut Date' or col == 'Retire Date':
                            col1.write(f"**{col}**")
                            value = filtered_row[col]
                            if pd.isna(value):  # jika kosong/NaN
                                formatted_date = None
                            else:
                                try:
                                    # ubah dulu ke string biar aman
                                    value_str = str(value)
                                    date = datetime.datetime.strptime(value_str, "%d/%m/%Y").date()
                                    formatted_date = date.strftime("%B %d, %Y")  # contoh format "January 01, 2025"
                                except ValueError:
                                    formatted_date = "?"
                            col2.write(f"{formatted_date}")

                elif usn == v_usn:
                    for col in filtered_df.columns:
                        if col != 'Picture' and col!='::auto_unique_id::' :
                            col1, col2 = st.columns([1, 2])  # kolom 1 untuk label, kolom 2 untuk value
                            col1.write(f"**{col}**")
                            col2.write(f"{filtered_row[col]}")
                
                button_col1, button_col2 = st.columns([1,5])

                with button_col1:
                    if st.button("Edit"):
                        st.session_state.back = st.session_state.page
                        st.session_state.page = "Edit"
                        st.session_state.data = filtered_row
                        st.session_state.existing_data = existing_data
                        st.rerun()

                with button_col2:
                    # Gunakan st.form atau st.session_state untuk handle confirmation
                    if 'delete_confirm' not in st.session_state:
                        st.session_state.delete_confirm = False
                    
                    if not st.session_state.delete_confirm:
                        if st.button("Delete", type="secondary"):
                            st.session_state.delete_confirm = True
                            st.rerun()
                    else:
                        st.warning("🗑️ Are you sure? This cannot be undone.")
                        
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("YES DELETE", type="primary"):
                                # Delete logic here
                                try:
                                    deleted_pic_id = selected['Name (Alphabet)'].iloc[0]
                                    join_name = deleted_pic_id
                                    clean_name = re.sub(r'[^\w]','', join_name)
                                    
                                    if usn == n_usn:
                                        clean_name = "N" + clean_name
                                    elif usn == v_usn:
                                        clean_name = "V" + clean_name
                                    
                                    # Delete dari Cloudinary
                                    delete_success = delete_cloudinary_image(clean_name)
                                    
                                    if delete_success:
                                        # Delete dari DataFrame
                                        if usn == n_usn:
                                            delete_df = existing_data[existing_data['Name (Kanji)'] != selected['Name (Kanji)'].iloc[0]]
                                        elif usn == v_usn:
                                            delete_df = existing_data[existing_data['Name (Alphabet)'] != selected['Name (Alphabet)'].iloc[0]]
                                        
                                        # Update Google Sheets
                                        if usn == n_usn:
                                            conn.update(worksheet='NList', data=delete_df)
                                        else:    
                                            conn.update(worksheet='VList', data=delete_df)
                                        
                                        st.success("✅ Data berhasil dihapus!")
                                        # Reset state dan clear cache
                                        st.session_state.delete_confirm = False
                                        reset_cache()
                                        st.rerun()
                                    else:
                                        st.error("❌ Gagal menghapus gambar dari Cloudinary")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error saat delete: {e}")
            
                            with col_cancel:
                                if st.button("Cancel"):
                                    st.session_state.delete_confirm = False
                                    st.rerun()
            else:
                st.info("Klik salah satu baris untuk melihat detailnya.")


# =================
#  EDIT PAGE
# =================
elif st.session_state.page == 'Edit':
    # Load data once and store it in session state
    usn = st.session_state.usn
    if 'existing_data' not in st.session_state:
        st.session_state.existing_data = load_gsheet_data(usn)

    existing_data = st.session_state.existing_data
    update_df = st.session_state.data
    usn = st.session_state.usn
    left, mid, right = st.columns([1,2,2])

    if usn == n_usn:
        review_index = REVIEW_OPTS.index(update_df['Review']) if update_df['Review'] in REVIEW_OPTS else 0
        size_index = SIZE_OPTS.index(update_df['Size']) if update_df['Size'] in SIZE_OPTS else 0
        status_index = STATUS_OPTS.index(update_df['Status']) if update_df['Status'] in STATUS_OPTS else 0
    elif usn == v_usn:
        info_index = INFO.index(update_df['Status']) if update_df['Status'] in INFO else 0

    with left:
        if st.button("Back"):
            st.session_state.page = st.session_state.back
            st.rerun()

        if pd.isna(update_df['Name (Kanji)']):
            kanji = "None"
        else:
            kanji = update_df['Name (Kanji)']

        st.write(kanji)
        st.subheader(update_df['Name (Alphabet)'] + " (" + kanji + ") ")
        if pd.notna(update_df['Picture']):
            image_content = fetch_image(update_df['Picture'])
            if image_content:
                st.image(image_content, width=150)
        else:
            st.write("No picture available.")

        # 1. INPUT IMAGE
        new_pic = st.file_uploader("Change Image", type=['png', 'jpg', 'jpeg'])
        if new_pic is not None:
            st.image(new_pic, width = 150)

    with mid:
        if usn == n_usn:
            mleft, mright = st.columns([7,3])   
            # 2. INPUT REVIEW
            review_type = st.selectbox("Review", options=REVIEW_OPTS, index=review_index)

        # 3. INPUT NAME (ALPHABET)
        name_alpha = st.text_input(label="Nama (Alphabet)", value=update_df['Name (Alphabet)'])

        # 4. INPUT NAME (KANJI)
        if pd.isna(update_df['Name (Kanji)']):
            namek = ''
        else:
            namek = update_df['Name (Kanji)']
        name_kanji = st.text_input(label="Name (Kanji)", value=namek)

        if usn == n_usn:
            # 5. INPUT BIRTHDATE
            birth_date = st.date_input(
                "Birthdate",
                value=(
                    datetime.datetime.strptime(update_df["Birthdate"], "%d/%m/%Y").date()
                    if pd.notna(update_df["Birthdate"]) and update_df["Birthdate"] != "?"
                    else date.today()
                )
            )

            default_no_info = update_df['Birthdate'] == "?"

            birth_check = st.checkbox(
                "No Info - Birthdate",
                value=default_no_info
            )

            if birth_check:
                formatted_birthdate = "?"
            else:
                formatted_birthdate = birth_date.strftime("%d/%m/%Y")
            
            # 6. INPUT DEBUT DATE
            debut_date = st.date_input(
                "Debut Date",
                value=(
                    datetime.datetime.strptime(update_df["Debut Date"], "%d/%m/%Y").date()
                    if pd.notna(update_df["Debut Date"]) and update_df["Debut Date"] != "?"
                    else None
                )
            )

            debut_no_info = update_df['Debut Date'] == "?"

            debut_check = st.checkbox(
                "No Info - Debut Date",
                value=debut_no_info
            )

            if debut_check:
                formatted_debutDate = "?"
            else:
                formatted_debutDate = debut_date.strftime("%d/%m/%Y")
    
            with right:
                # 7. INPUT SIZE
                size = st.selectbox("Size", options=SIZE_OPTS, index=size_index)

                # 8. INPUT MEASUREMENT
                if update_df['Measurement'] != "?":
                    parts = update_df['Measurement'].split(" / ")  # ['A12', 'B34', 'C45']

                    # Number Extraction
                    bust = int(re.search(r'\d+', parts[0]).group())  # 12
                    waist = int(re.search(r'\d+', parts[1]).group())  # 34
                    hips = int(re.search(r'\d+', parts[2]).group())  # 45
                else:
                    bust=0
                    waist=0
                    hips=0

                b,bw,w,wh,h = st.columns([4,.5,4,.5,4])
                with b:
                    b_size = st.number_input("Bust", value=bust)
                with bw:
                    st.write("/")
                with w:
                    w_size = st.number_input("Waist", value=waist)
                with wh:
                    st.write("/")
                with h:
                    h_size = st.number_input("Hip", value=hips)
                
                measure_no_info = update_df['Measurement'] == '?'
                if st.checkbox("No Info - Measurement", value=measure_no_info):
                    measure = "?"
                else:
                    measure = f"B{b_size} / W{w_size} / H{h_size}"

                # 9. UPDATE HEIGHT
                if update_df['Height (cm)'] != "? cm":
                    updt_height = int(update_df['Height (cm)'].split(' ')[0])
                else:
                    updt_height = 0

                height = st.number_input("Height (cm)", value=updt_height)

                height_no_info = update_df['Height (cm)'] == '? cm'
                if st.checkbox("No Info - Height", value=height_no_info):
                    height = "?"
                
                #10. INPUT NOTES
                if update_df['Notes'] == "--":
                    cat = ""
                else:
                    cat = update_df['Notes']
                notes = st.text_area("Notes", value=cat)
                if notes == "" or notes == None :
                    notes = "--"

                status = st.selectbox("Status", options=STATUS_OPTS, index=status_index)

                if status == "Retired":
                    # 11. INPUT RETIRE DATE
                    retire = st.date_input(
                        "Retire",
                        value=(
                            datetime.datetime.strptime(update_df["Retire Date"], "%d/%m/%Y").date()
                            if pd.notna(update_df["Retire Date"]) and update_df["Retire Date"] != "-"
                            else datetime.date.today()
                        )
                    )
                    formatted_retire = retire.strftime("%d/%m/%Y")
                else:
                    formatted_retire = "-"
                
                if st.button("Done "):
                    conn = st.session_state.conn
                    test = existing_data.copy()
                    if(formatted_birthdate!="?"):
                        dob = pd.to_datetime(formatted_birthdate, format=f'%d/%m/%Y')
                    
                    if(formatted_debutDate != '?'):
                        dod = pd.to_datetime(formatted_debutDate, format=f'%d/%m/%Y')
                    
                    if(formatted_retire != '-'):
                        dor = pd.to_datetime(formatted_retire, format=f'%d/%m/%Y')

                    if formatted_birthdate == "?":
                        age = "?"
                    else:
                        age = date.today().year - dob.year

                    if formatted_debutDate == "?" and status != "Retired":
                        debut = '?'
                    elif formatted_debutDate != "?" and status != "Retired":
                        period_year = date.today().year - dod.year
                        period_month = date.today().month - dod.month
                        if date.today().day < dod.day:
                            period_month -= 1

                        if period_month < 0:
                            period_year -= 1
                            period_month += 12
                        
                        if period_month == 0:
                            debut = f"{period_year} Year"
                        else:
                            debut = f"{period_year} Year {period_month} Month"
                    elif formatted_debutDate == "?" and status == "Retired":
                        debut = "?"
                    elif formatted_debutDate != "?" and status == "Retired":
                        period_year = dor.year - dod.year
                        period_month = dor.month - dod.month
                        if dor.day < dod.day:
                            period_month -= 1

                        if period_month < 0:
                            period_year -= 1
                            period_month += 12
                        
                        if period_month == 0:
                            debut = f"{period_year} Year"
                        else:
                            debut = f"{period_year} Year {period_month} Month"
                
                    join_name = name_alpha
                    clean_name = re.sub(r'[^\w]','',join_name)
                    clean_name = "N" + clean_name

                    old_pic = update_df['Picture']

                    # Ambil bagian terakhir setelah split '/'
                    filename = old_pic.split('/')[-1]

                    # Hapus extension .png
                    name_without_extension = filename.split('.')[0]

                    if new_pic is not None and name_without_extension != "Placeholder":
                        delete_cloudinary_image(name_without_extension)
                        link = upload_to_database(new_pic, clean_name)
                        test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Picture"] = link
                    elif new_pic is not None and name_without_extension == "Placeholder":
                        link = upload_to_database(new_pic, clean_name)
                        test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Picture"] = link
                    else:
                        if name_without_extension != 'Placeholder' and name_without_extension != clean_name:
                            link = rename_cloudinary_image(name_without_extension, clean_name)
                            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Picture"] = link

                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Name (Alphabet)"] = name_alpha
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Review"] = review_type
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Birthdate"] = formatted_birthdate
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Debut Date"] = formatted_debutDate
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Size"] = size
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Measurement"] = measure

                    test["Notes"] = test["Notes"].astype("object")
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Notes"] = notes

                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Height (cm)"] = str(height) + ' cm'
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Retire Date"] = formatted_retire
                    test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Name (Kanji)"] = name_kanji

                    conn.update(worksheet='NList', data=test)
                    st.session_state.page = 'Home'
                    reset_cache()
        
        elif usn == v_usn:
            status_type = st.selectbox("Status", options=INFO, index=info_index)
            if st.button("Done"):
                conn = st.session_state.conn
                test = existing_data.copy()
                join_name = name_alpha  # ⬅️ Tambah .iloc[0]
                clean_name = re.sub(r'[^\w]','',join_name)
                clean_name = "V" + clean_name

                old_pic = update_df['Picture']

                # Ambil bagian terakhir setelah split '/'
                filename = old_pic.split('/')[-1]

                # Hapus extension .png
                name_without_extension = filename.split('.')[0]

                st.write(name_without_extension, clean_name)
                if new_pic is not None and name_without_extension != "Placeholder":
                    delete_cloudinary_image(clean_name)
                    link = upload_to_database(new_pic, clean_name)
                    test.loc[test["Name (Alphabet)"] == update_df["Name (Alphabet)"], "Picture"] = link
                elif new_pic is not None and name_without_extension == "Placeholder":
                    link = upload_to_database(new_pic, clean_name)
                    test.loc[test["Name (Alphabet)"] == update_df["Name (Alphabet)"], "Picture"] = link
                else:
                    if name_without_extension != 'Placeholder' and name_without_extension != clean_name:
                        link = rename_cloudinary_image(name_without_extension, clean_name)
                        test.loc[test["Name (Alphabet)"] == update_df["Name (Alphabet)"], "Picture"] = link
                    
                test.loc[test["Name (Alphabet)"] == update_df["Name (Alphabet)"], "Status"] = status_type
                test.loc[test["Name (Alphabet)"] == update_df["Name (Alphabet)"], "Name (Kanji)"] = name_kanji
                test.loc[test["Name (Alphabet)"] == update_df["Name (Alphabet)"], "Name (Alphabet)"] = name_alpha
                
                conn.update(worksheet='VList', data=test)
                st.session_state.page = 'Home'
                reset_cache()

elif st.session_state.page == 'Gallery':
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Actress List 😊</h1>", unsafe_allow_html=True)
    st.set_page_config(layout="wide")

    left, mid, right = st.columns([.3, 2, .3])

    # Koneksi ke Google Sheets - baca semua kolom
    conn = st.connection("gsheets", type=GSheetsConnection)
    List = conn.read(worksheet="NList", usecols=list(range(14)))

    # Ambil semua kolom sesuai field yang dipakai
    pics = List['Picture'].dropna().tolist()
    name = List['Name (Alphabet)'].dropna().tolist()
    kanji = List['Name (Kanji)'].dropna().tolist()

    # Ambil kolom lainnya dengan nama yang tepat
    review = List['Review'].dropna().tolist() if 'Review' in List.columns else [""] * len(pics)
    birthdate = List['Birthdate'].dropna().tolist() if 'Birthdate' in List.columns else [""] * len(pics)
    debut_date = List['Debut Date'].dropna().tolist() if 'Debut Date' in List.columns else [""] * len(pics)
    size = List['Size'].dropna().tolist() if 'Size' in List.columns else [""] * len(pics)
    measurement = List['Measurement'].dropna().tolist() if 'Measurement' in List.columns else [""] * len(pics)
    height = List['Height (cm)'].dropna().tolist() if 'Height (cm)' in List.columns else [""] * len(pics)
    notes = List['Notes'].dropna().tolist() if 'Notes' in List.columns else [""] * len(pics)
    age = List['Age'].dropna().tolist() if 'Age' in List.columns else [""] * len(pics)
    debut_period = List['Debut Period'].dropna().tolist() if 'Debut Period' in List.columns else [""] * len(pics)
    retire_date = List['Retire Date'].dropna().tolist() if 'Retire Date' in List.columns else [""] * len(pics)
    status = List['Status'].dropna().tolist() if 'Status' in List.columns else ["Active"] * len(pics)

    count = len(pics)
    N_PICS = count


    # Langsung gunakan list pics sebagai sumber gambar
    if "pics" not in st.session_state:
        st.session_state.pics = pics
    if "name" not in st.session_state:
        st.session_state.name = name
    if "kanji" not in st.session_state:
        st.session_state.kanji = kanji

    # Simpan semua data kolom di session state
    if "all_data" not in st.session_state:
        st.session_state.all_data = {
            'birthdate': birthdate,
            'debut_date': debut_date,
            'size': size,
            'measurement': measurement,
            'height': height,
            'notes': notes,
            'age': age,
            'debut_period': debut_period,
            'retire_date': retire_date,
            'status': status,
            'review' : review
        }

    # Fungsi untuk menghitung usia berdasarkan birthdate
    def calculate_age(birthdate_str):
        try:
            birth_date = datetime.strptime(birthdate_str, '%B %d, %Y')
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return None

    # Dialog untuk menampilkan detail lengkap
    @st.dialog("🎬 Actress Details", width="medium")
    def show_actress_details(index):
        cat_url = st.session_state.pics[index]
        name_text = st.session_state.name[index] if index < len(st.session_state.name) else ""
        kanji_text = st.session_state.kanji[index] if index < len(st.session_state.kanji) else ""
        
        # Layout utama dengan gambar dan info dasar
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(cat_url, width=200)
            st.markdown(f"### {name_text}")
            st.markdown(f"# {kanji_text}")
            
        
        with col2:
            # Info dasar dalam metrics
            st.markdown("### Basic Information")
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                # Age
                age_text = st.session_state.all_data['age'][index] if index < len(st.session_state.all_data['age']) else ""
                if not age_text and index < len(st.session_state.all_data['birthdate']):
                    # Calculate age from birthdate jika age tidak ada
                    calculated_age = calculate_age(st.session_state.all_data['birthdate'][index])
                    if calculated_age:
                        age_text = f"{calculated_age}"
                
                if age_text:
                    st.metric("Age", f"{age_text} years")
                
                # Birthdate
                if index < len(st.session_state.all_data['birthdate']):
                    st.metric("Birthdate", st.session_state.all_data['birthdate'][index] or "N/A")
                
                # Height
                if index < len(st.session_state.all_data['height']):
                    st.metric("Height", st.session_state.all_data['height'][index] or "N/A")
            
            with info_col2:
                
                # Size
                if index < len(st.session_state.all_data['size']):
                    st.metric("Size", st.session_state.all_data['size'][index] or "N/A")
                
                # Review
                if index < len(st.session_state.all_data['review']):
                    st.metric("Review", st.session_state.all_data['review'][index] or "N/A")

                # Status dengan badge warna
                status_text = st.session_state.all_data['status'][index] if index < len(st.session_state.all_data['status']) else "Active"
                if status_text.lower() == "active":
                    st.metric("Status", f"🟢 {status_text}")
                elif status_text.lower() == "retired":
                    st.metric("Status", f"🔴 {status_text}")
                else:
                    st.metric("Status", f"⚪ {status_text}")

        st.markdown("---")
        
        # Measurement dan Physical Info
        st.markdown("### Physical Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if index < len(st.session_state.all_data['measurement']) and st.session_state.all_data['measurement'][index]:
                st.markdown("#### 📏 Measurements")
                st.info(st.session_state.all_data['measurement'][index])
        
        with col4:
            # Additional physical info
            if index < len(st.session_state.all_data['size']) and st.session_state.all_data['size'][index]:
                st.markdown("#### 📐 Size")
                st.info(f"**{st.session_state.all_data['size'][index]}**")
        
        st.markdown("---")
        
        # Career Timeline
        st.markdown("### Career Timeline")
        
        timeline_col1, timeline_col2, timeline_col3 = st.columns(3)
        
        with timeline_col1:
            if index < len(st.session_state.all_data['debut_date']) and st.session_state.all_data['debut_date'][index]:
                st.markdown("#### 🎭 Debut")
                st.write(st.session_state.all_data['debut_date'][index])
        
        with timeline_col2:
            if index < len(st.session_state.all_data['debut_period']) and st.session_state.all_data['debut_period'][index]:
                st.markdown("#### ⏳ Experience")
                st.write(st.session_state.all_data['debut_period'][index])
        
        with timeline_col3:
            if index < len(st.session_state.all_data['retire_date']) and st.session_state.all_data['retire_date'][index]:
                st.markdown("#### 🏁 Retire Date")
                st.write(st.session_state.all_data['retire_date'][index])
            else:
                st.markdown("#### 🏁 Retire Date")
                st.write("Still Active")
        
        st.markdown("---")
        
        # Notes/Review
        if index < len(st.session_state.all_data['notes']) and st.session_state.all_data['notes'][index]:
            st.markdown("### 📝 Review & Notes")
            st.warning(st.session_state.all_data['notes'][index])
        
        st.markdown("---")
        
        # Personal Notes Section
        st.write("### 📖 Your Personal Notes")
        personal_notes = st.text_area(
            "Add your own notes about this actress...", 
            placeholder="Write your thoughts, reviews, or observations about this actress...",
            key=f"personal_notes_{index}"
        )
        
        col7, col8 = st.columns(2)
        with col7:
            if st.button("💾 Save Notes", use_container_width=True, key=f"save_{index}"):
                if personal_notes:
                    if "personal_notes" not in st.session_state:
                        st.session_state.personal_notes = {}
                    st.session_state.personal_notes[index] = {
                        "name": name_text,
                        "kanji": kanji_text,
                        "notes": personal_notes,
                        "image": cat_url
                    }
                    st.success("Notes saved successfully!")
                else:
                    st.warning("Please write some notes before saving!")
        
        with col8:
            if st.button("Close", use_container_width=True, key=f"close_{index}"):
                st.rerun()

    with st.sidebar:
        st.header("Filters")
        show_active = st.checkbox("Active", value=True)
        show_retired = st.checkbox("Retired", value=True)
        
        # Tampilkan personal notes jika ada
        if "personal_notes" in st.session_state:
            st.markdown("---")
            st.subheader("📖 Your Notes")
            for idx, note_data in st.session_state.personal_notes.items():
                with st.expander(f"{note_data['name']}"):
                    st.image(note_data['image'], width=60)
                    st.write(note_data['notes'])

    # CSS untuk styling card yang estetik
    st.markdown("""
    <style>
        .cat-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 20px 15px;
            margin: 10px;
            border-radius: 15px;
            border: 2px solid #e0e0e0;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            min-height: 280px;
            width: 100%;
            max-width: 220px;
            cursor: pointer;
        }
        .cat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            border-color: #ff6b6b;
        }
        .cat-image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            width: 100%;
            height: 150px;
            overflow: hidden;
            border-radius: 10px;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
        }
        .cat-image {
            border-radius: 8px;
            object-fit: cover;
            max-width: 150px;
            max-height: 150px;
            border: 2px solid #ff6b6b;
        }
        .cat-name {
            font-weight: 700;
            font-size: 16px;
            color: #2c3e50;
            margin: 5px 0;
            line-height: 1.3;
        }
        .cat-kanji {
            font-size: 18px;
            color: #e74c3c;
            margin: 5px 0;
            font-weight: 500;
            line-height: 1.3;
        }
        .card-divider {
            width: 50px;
            height: 2px;
            background: linear-gradient(90deg, #ff6b6b, #ffa726);
            margin: 8px 0;
            border-radius: 2px;
        }
        .card-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 5px;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

    # Pastikan ada gambar yang ditampilkan
    with mid:
        if st.session_state.pics:
            n_rows = (N_PICS + 5 - 1) // 5
            rows = [st.columns(5) for _ in range(n_rows)]
            cols = [column for row in rows for column in row]

            displayed_count = 0
            
            for i, (col, cat_url) in enumerate(zip(cols, st.session_state.pics)):
                # Filter berdasarkan status
                status_text = st.session_state.all_data['status'][i] if i < len(st.session_state.all_data['status']) else "Active"
                status_lower = status_text.lower()
                
                if (status_lower == "active" and not show_active) or (status_lower == "retired" and not show_retired):
                    continue
                    
                try:
                    with col:
                        name_text = st.session_state.name[i] if i < len(st.session_state.name) else ""
                        kanji_text = st.session_state.kanji[i] if i < len(st.session_state.kanji) else ""
                        
                        # Buat card dengan HTML lengkap
                        card_html = f"""
                        <div class="card-wrapper">
                            <div class="cat-card">
                                <div class="cat-image-container">
                                    <img src="{cat_url}" class="cat-image" width="150" height="150">
                                </div>
                                <div class="card-divider"></div>"""
                        
                        if name_text and kanji_text:
                            card_html += f"""<div class="cat-name">{name_text}</div>
                                <div class="cat-kanji">{kanji_text}</div>
                            """
                        elif name_text:
                            card_html += f'<div class="cat-name">{name_text}</div>'
                        elif kanji_text:
                            card_html += f'<div class="cat-kanji">{kanji_text}</div>'
                        
                        card_html += """</div>
                        </div>
                        """
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Button untuk membuka dialog
                        if st.button("View Details", key=f"btn_{i}", use_container_width=True):
                            show_actress_details(i)
                        
                        displayed_count += 1
                            
                except Exception as e:
                    with col:
                        error_html = """
                        <div class="card-wrapper">
                            <div class="cat-card">
                                <div style="text-align: center; color: #e74c3c;">
                                    <div style="font-size: 24px; margin-bottom: 10px;">😿</div>
                                    <div style="font-size: 14px;">Gagal memuat gambar</div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(error_html, unsafe_allow_html=True)
            
            if displayed_count == 0:
                st.warning("No actresses match the selected filters.")
                
        else:
            st.warning("Tidak ada gambar yang ditemukan di kolom 'Picture'")







