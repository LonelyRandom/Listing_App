import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from st_aggrid.shared import GridUpdateMode, DataReturnMode
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from io import StringIO
import datetime
import re
from upload_image import up_to_drive

if "page" not in st.session_state:
    st.session_state.page = "Home"


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
def load_gsheet_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    NList = conn.read(worksheet="NList", usecols=list(range(14)), ttl=5)
    return NList

# Load data once and store it in session state
if 'existing_data' not in st.session_state:
    st.session_state.existing_data = load_gsheet_data()

existing_data = st.session_state.existing_data.copy()

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

# Cache all images
if 'all_images' not in st.session_state:
    st.session_state.all_images = cache_all_images(existing_data)

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

if st.session_state.page == 'Home':

    page = st.sidebar.radio("Pilih Halaman:", ["Home", "Edit", "Data Pegawai"])
    st.title("📃 List 📃") 
    col1,col2 = st.columns([1,1])
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
    gb.configure_column("Name", header_name="Name (Kanji)", width=75,  cellStyle={'textAlign': 'left'})

    # Opsi tambahan
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    gb.configure_grid_options(alwaysShowHorizontalScroll=True, suppressHorizontalScroll=False, enableRangeSelection=True, pagination=True, paginationPageSize=10000, domLayout='normal')



    # Bangun grid option
    gridOptions = gb.build()

    # Tampilkan di Streamlit
    with col1:
        # st.subheader("💼 Data Pegawai")
        agdf = AgGrid(
            df_filter,
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


            selected_name = selected.iloc[0]["Name (Kanji)"]

            # Filter df_detail berdasarkan nama yang dipilih
            filtered_df = existing_data[existing_data["Name (Kanji)"] == selected_name].copy()
            picture = filtered_df['Picture'].iloc[0]
            filtered_row = filtered_df.iloc[0]  # satu row
            picture_content = st.session_state.all_images.get(selected_name)

            with sub_col2:
                if picture_content:
                    st.image(picture_content, width=300)
                else:
                    st.write("No picture available.")

            st.subheader(f"**Description:** ")

            for col in filtered_df.columns:
                col1, col2 = st.columns([1, 2])  # kolom 1 untuk label, kolom 2 untuk value
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
                            formatted_date = "-"

                    col2.write(f"{formatted_date}")

            
            button_col1, button_col2 = st.columns([1,5])

            with button_col1:
                if st.button("Edit"):
                    st.session_state.back = st.session_state.page
                    st.session_state.page = "Edit"
                    st.session_state.data = filtered_row
                    st.rerun()

            with button_col2:
                st.button("Delete")

        else:
            st.info("Klik salah satu baris untuk melihat detailnya.")

elif st.session_state.page == 'Edit':
    update_df = st.session_state.data
    left, mid, right = st.columns([1,2,2])
    review_index = REVIEW_OPTS.index(update_df['Review']) if update_df['Review'] in REVIEW_OPTS else 0
    size_index = SIZE_OPTS.index(update_df['Size']) if update_df['Size'] in SIZE_OPTS else 0
    status_index = STATUS_OPTS.index(update_df['Status'] if update_df['Status'] in STATUS_OPTS else 0)

    with left:
        if st.button("Back"):
            st.session_state.page = st.session_state.back
            st.rerun()
        st.subheader(update_df['Name (Alphabet)'] + " (" + update_df['Name (Kanji)'] + ") ")
        if pd.notna(update_df['Picture']):
            image_content = fetch_image(update_df['Picture'])
            if image_content:
                st.image(image_content, width=300)
        else:
            st.write("No picture available.")

        # 1. INPUT IMAGE
        new_pic = st.file_uploader("Change Image", type=['png', 'jpg', 'jpeg'])
        if new_pic is not None:
            st.image(new_pic)

    with mid:
        mleft, mright = st.columns([7,3])
        # 2. INPUT REVIEW
        review_type = st.selectbox("Review", options=REVIEW_OPTS, index=review_index)

        # 3. INPUT NAME (ALPHABET)
        name_alpha = st.text_input(label="Nama (Alphabet)", value=update_df['Name (Alphabet)'])

        # 4. INPUT NAME (KANJI)
        name_kanji = st.text_input(label="Name (Kanji)", value=update_df['Name (Kanji)'])

        # 5. INPUT BIRTHDATE
        birth_date = st.date_input(
            "Birthdate",
            value=(
                datetime.datetime.strptime(update_df["Birthdate"], "%d/%m/%Y").date()
                if pd.notna(update_df["Birthdate"]) and update_df["Birthdate"] != ""
                else datetime.date.today()
            )
        )
        if st.checkbox("No Info - Birthdate"):
            formatted_birthdate = "?"
        else:
            formatted_birthdate = birth_date.strftime("%B %d, %Y")
        
        st.write(formatted_birthdate)

        # 6. INPUT DEBUT DATE
        debut_date = st.date_input(
            "Debut Date",
            value=(
                datetime.datetime.strptime(update_df["Debut Date"], "%d/%m/%Y").date()
                if pd.notna(update_df["Debut Date"]) and update_df["Debut Date"] != ""
                else datetime.date.today()
            )
        )
        if st.checkbox("No Info - Debut Date"):
            formatted_debutDate = "?"
        else:
            formatted_debutDate = debut_date.strftime("%B %d, %Y")
    
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
        
        if st.checkbox("No Info - Measurement"):
            measure = "?"
        else:
            measure = f"B{b_size} / W{w_size} / H{h_size}"

        # 9. UPDATE HEIGHT
        if update_df['Height (cm)'] != "?":
            updt_height = int(update_df['Height (cm)'].split(' ')[0])
        else:
            updt_height = 0

        height = st.number_input("Height (cm)", value=updt_height)

        if st.checkbox("No Info - Height"):
            height = "?"
        
        #10. INPUT NOTES
        notes = st.text_area("Notes", value=update_df['Notes'])

        status = st.selectbox("Status", options=STATUS_OPTS, index=status_index)

        if status == "Retired":
            # 11. INPUT RETIRE DATE
            retire = st.date_input(
                "Retire",
                value=(
                    datetime.datetime.strptime(update_df["Retire Date"], "%d/%m/%Y").date()
                    if pd.notna(update_df["Retire Date"]) and update_df["Retire Date"] != ""
                    else datetime.date.today()
                )
            )
            formatted_retire = retire.strftime("%B %d, %Y")
            st.write(formatted_retire)
        else:
            formatted_retire = "-"
        
        if st.button("Done"):
            test = existing_data.copy()
            join_name = update_df['Name (Alphabet)'] + " (" + update_df['Name (Kanji)']+ ")"
            if new_pic is not None:
                link = up_to_drive(new_pic, join_name)
                test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Picture"] = link

            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Name (Alphabet)"] = name_alpha
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Review"] = review_type
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Birthdate"] = formatted_birthdate
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Debut Date"] = formatted_debutDate
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Size"] = size
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Measurement"] = measure
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Notes"] = notes
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Height (cm)"] = height
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Retire Date"] = formatted_retire
            test.loc[test["Name (Kanji)"] == update_df["Name (Kanji)"], "Name (Kanji)"] = name_kanji
            st.write(test)










