import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from municipality_population_and_coords import municipality_data

st.set_page_config(layout="wide")

# ===========================
# AUTHENTICATION SECTION
# ===========================
# Simple authentication - replace with more robust method for production
def check_authority_login():
    """Simple login check for authorities"""
    # Try to use secrets first (for Streamlit Cloud)
    try:
        auth_password = st.secrets["authority_password"]
    except:
        # Fallback to environment variable or default
        auth_password = "2026"  # Change this to your preferred password
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.warning("⚠️ This dashboard is for authorized personnel only.")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.markdown("### Authority Login")
            password = st.text_input("Enter password:", type="password", key="auth_password")
            
            if st.button("Login", key="login_button"):
                if password == auth_password:
                    st.session_state.authenticated = True
                    st.success("✓ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Access denied.")
        
        st.stop()

# Check authentication
check_authority_login()

# Personality mapping
PERSONALITY_MAPPING = {
    'REACT': 'The Decisive Catalyst',
    'TRUST': 'The Guided Follower',
    'INDEPENDENT': 'The Independent Pathfinder',
    'ADAPTABILITY': 'The Intuitive Adapter',
    'MOBILITY': 'The Agile Go-Getter',
    'SAFETY': 'The Cautious Survivor',
    'COMMUNITY': 'The Helping Heart',
    'PREPAREDNESS': 'The Equipped Mover'
}

SCORE_COLUMN_TO_PERSONALITY = {
    'score_react': 'REACT',
    'score_trust': 'TRUST',
    'score_indep': 'INDEPENDENT',
    'score_adapt': 'ADAPTABILITY',
    'score_mobil': 'MOBILITY',
    'score_safety': 'SAFETY',
    'score_commu': 'COMMUNITY',
    'score_prep': 'PREPAREDNESS'
}

SERVICE_AREA_LABEL = 'Wellbeing Services County / Special Area'

COUNTY_TO_MUNICIPALITIES = {
    "Central Finland": [
        "Hankasalmi", "Joutsa", "Jyväskylä", "Jämsä", "Kannonkoski", "Karstula", "Keuruu",
        "Kinnula", "Kivijärvi", "Konnevesi", "Kyyjärvi", "Laukaa", "Luhanka", "Multia",
        "Muurame", "Petäjävesi", "Pihtipudas", "Saarijärvi", "Toivakka", "Uurainen",
        "Viitasaari", "Äänekoski"
    ],
    "Central Ostrobothnia": [
        "Halsua", "Kannus", "Kaustinen", "Kokkola", "Lestijärvi", "Perho", "Toholampi", "Veteli"
    ],
    "Central Uusimaa": ["Hyvinkää", "Järvenpää", "Nurmijärvi", "Mäntsälä", "Tuusula", "Pornainen"],
    "East Uusimaa": ["Askola", "Lapinjärvi", "Loviisa", "Myrskylä", "Porvoo", "Pukkila", "Sipoo"],
    "Kainuu": ["Hyrynsalmi", "Kajaani", "Kuhmo", "Paltamo", "Puolanka", "Ristijärvi", "Sotkamo", "Suomussalmi"],
    "Kanta-Häme": [
        "Forssa", "Hattula", "Hausjärvi", "Humppila", "Hämeenlinna", "Janakkala", "Jokioinen",
        "Loppi", "Riihimäki", "Tammela", "Ypäjä"
    ],
    "Kymenlaakso": ["Hamina", "Kotka", "Kouvola", "Miehikkälä", "Pyhtää", "Virolahti"],
    "Lapland": [
        "Enontekiö", "Inari", "Kemi", "Kemijärvi", "Keminmaa", "Kittilä", "Kolari", "Muonio",
        "Pelkosenniemi", "Pello", "Posio", "Ranua", "Rovaniemi", "Salla", "Savukoski", "Simo",
        "Sodankylä", "Tervola", "Tornio", "Utsjoki", "Ylitornio"
    ],
    "North Karelia": [
        "Heinävesi", "Ilomantsi", "Joensuu", "Juuka", "Kitee", "Kontiolahti", "Lieksa", "Liperi",
        "Nurmes", "Outokumpu", "Polvijärvi", "Rääkkylä", "Tohmajärvi"
    ],
    "North Ostrobothnia": [
        "Alavieska", "Haapajärvi", "Haapavesi", "Hailuoto", "Ii", "Kalajoki", "Kempele", "Kuusamo",
        "Kärsämäki", "Liminka", "Lumijoki", "Merijärvi", "Muhos", "Nivala", "Oulainen", "Oulu",
        "Pudasjärvi", "Pyhäjoki", "Pyhäjärvi", "Pyhäntä", "Raahe", "Reisjärvi", "Sievi", "Siikajoki",
        "Siikalatva", "Taivalkoski", "Tyrnävä", "Utajärvi", "Vaala", "Ylivieska"
    ],
    "North Savo": [
        "Iisalmi", "Joroinen", "Kaavi", "Keitele", "Kiuruvesi", "Kuopio", "Lapinlahti", "Leppävirta",
        "Pielavesi", "Rautalammi", "Rautavaara", "Siilinjärvi", "Sonkajärvi", "Suonenjoki", "Tervo",
        "Tuusniemi", "Varkaus", "Vesanto", "Vieremä"
    ],
    "Ostrobothnia": [
        "Kaskinen", "Korsnäs", "Kristinestad", "Kronoby", "Laihia", "Larsmo", "Malax", "Korsholm",
        "Närpes", "Pedersöre", "Jakobstad", "Nykarleby", "Vaasa", "Vörå"
    ],
    "Pirkanmaa": [
        "Akaa", "Hämeenkyrö", "Ikaalinen", "Juupajoki", "Kangasala", "Kihniö", "Kuhmoinen", "Lempäälä",
        "Mänttä-Vilppula", "Nokia", "Orivesi", "Parkano", "Pirkkala", "Punkalaidun", "Pälkäne",
        "Ruovesi", "Sastamala", "Tampere", "Urjala", "Valkeakoski", "Vesilahti", "Virrat", "Ylöjärvi"
    ],
    "Päijät-Häme": ["Asikkala", "Hartola", "Heinola", "Hollola", "Iitti", "Kärkölä", "Lahti", "Orimattila", "Padasjoki", "Sysmä"],
    "Satakunta": [
        "Eura", "Eurajoki", "Harjavalta", "Huittinen", "Jämijärvi", "Kankaanpää", "Karvia", "Kokemäki",
        "Merikarvia", "Nakkila", "Pomarkku", "Pori", "Rauma", "Siikainen", "Säkylä", "Ulvila"
    ],
    "South Karelia": ["Imatra", "Lappeenranta", "Lemi", "Luumäki", "Parikkala", "Rautjärvi", "Ruokolahti", "Savitaipale", "Taipalsaari"],
    "South Ostrobothnia": [
        "Alajärvi", "Alavus", "Evijärvi", "Ilmajoki", "Isojoki", "Isokyrö", "Karijoki", "Kauhajoki",
        "Kauhava", "Kuortane", "Kurikka", "Lappajärvi", "Lapua", "Seinäjoki", "Soini", "Teuva",
        "Vimpeli", "Ähtäri"
    ],
    "South Savo": ["Enonkoski", "Hirvensalmi", "Juva", "Kangasniemi", "Mikkeli", "Mäntyharju", "Pertunmaa", "Pieksämäki", "Puumala", "Rantasalmi", "Savonlinna", "Sulkava"],
    "Southwest Finland": [
        "Aura", "Kaarina", "Kimitoön", "Koski Tl", "Kustavi", "Laitila", "Lieto", "Loimaa", "Marttila",
        "Masku", "Mynämäki", "Naantali", "Nousiainen", "Oripää", "Paimio", "Pargas", "Pyhäranta",
        "Pöytyä", "Raisio", "Rusko", "Salo", "Sauvo", "Somero", "Taivassalo", "Turku", "Uusikaupunki",
        "Vehmaa"
    ],
    "Vantaa and Kerava": ["Vantaa", "Kerava"],
    "West Uusimaa": ["Espoo", "Hanko", "Ingå", "Karkkila", "Kauniainen", "Kirkkonummi", "Lohja", "Raseborg", "Siuntio", "Vihti"],
    "City of Helsinki": ["Helsinki"],
    "Åland": [
        "Brändö", "Eckerö", "Finström", "Föglö", "Geta", "Hammarland", "Jomala", "Kumlinge",
        "Kökar", "Lemland", "Lumparland", "Mariehamn", "Saltvik", "Sottunga", "Sund", "Vårdö"
    ]
}

MUNICIPALITY_TO_COUNTY = {
    municipality: county
    for county, municipalities in COUNTY_TO_MUNICIPALITIES.items()
    for municipality in municipalities
}

MUNICIPALITY_TO_COUNTY.update({
    "Inkoo": "West Uusimaa",
    "Raasepori": "West Uusimaa"
})

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data():
    """Load final player and decision data from GitHub or local files."""
    # GitHub raw content URLs
    GITHUB_BASE = "https://raw.githubusercontent.com/leyixu21/GCC2026_FOURSIGHT/main"
    DECISIONS_URL = f"{GITHUB_BASE}/data/final/decisions_rows.csv"
    PLAYERS_URL = f"{GITHUB_BASE}/data/final/players_rows.csv"
    
    try:
        # Try to load from GitHub
        decisions = pd.read_csv(DECISIONS_URL)
        players = pd.read_csv(PLAYERS_URL)
    except Exception as e:
        # Fallback to local files
        st.warning(f"Could not load from GitHub: {e}. Using local files...")
        decisions = pd.read_csv("data/final/decisions_rows.csv")
        players = pd.read_csv("data/final/players_rows.csv")
    
    return decisions, players

@st.cache_data
def load_questions_and_options():
    """Load final questions, options, and authority info from GitHub or local files."""
    # GitHub raw content URLs
    GITHUB_BASE = "https://raw.githubusercontent.com/leyixu21/GCC2026_FOURSIGHT/main"
    QUESTIONS_URL = f"{GITHUB_BASE}/data/final/questions_rows.csv"
    OPTIONS_URL = f"{GITHUB_BASE}/data/final/options_rows.csv"
    AUTHORITY_INFO_URL = f"{GITHUB_BASE}/data/final/authority_info.csv"
    
    try:
        # Try to load from GitHub
        questions = pd.read_csv(QUESTIONS_URL)
        options = pd.read_csv(OPTIONS_URL)
        authority_info = pd.read_excel(AUTHORITY_INFO_URL)
    except Exception as e:
        # Fallback to local files
        st.warning(f"Could not load from GitHub: {e}. Using local files...")
        questions = pd.read_csv("data/final/questions_rows.csv")
        options = pd.read_csv("data/final/options_rows.csv")
        authority_info = pd.read_excel("data/final/authority_info.csv")
    
    return questions, options, authority_info

@st.cache_data
def prepare_complete_responses(decisions, players, questions):
    """Keep only players with a full set of answered questions."""
    expected_question_count = questions['id'].nunique()
    answered_question_counts = decisions.groupby('player_id')['question_id'].nunique()
    complete_player_ids = answered_question_counts[answered_question_counts == expected_question_count].index

    decisions = decisions[decisions['player_id'].isin(complete_player_ids)].copy()
    players = players[players['id'].isin(complete_player_ids)].copy()
    players['wellbeing_services_county'] = players['municipality'].map(MUNICIPALITY_TO_COUNTY).fillna('Unmapped municipalities')

    return decisions, players, expected_question_count


def summarize_boolean_feature(dataframe, column_name, label_name):
    """Prepare yes/no counts for player profile boolean attributes."""
    feature_counts = (
        dataframe[column_name]
        .fillna(False)
        .astype(str)
        .str.lower()
        .map({'true': 'Yes', 'false': 'No'})
        .fillna('No')
        .value_counts()
        .reindex(['Yes', 'No'], fill_value=0)
        .rename_axis(label_name)
        .reset_index(name='Count')
    )
    return feature_counts


DIMENSION_DEFINITIONS = pd.DataFrame([
    {"No.": 1, "Dimension": "REACT", "Definition": "How quickly a person responds in a crisis"},
    {"No.": 2, "Dimension": "TRUST", "Definition": "Tendency to follow official guidance"},
    {"No.": 3, "Dimension": "INDEPENDENT", "Definition": "Self-directed decision-making and evacuation without external support"},
    {"No.": 4, "Dimension": "MOBILITY", "Definition": "Inclination to move and use organized transportation systems"},
    {"No.": 5, "Dimension": "SAFETY", "Definition": "Preference for low-risk decisions"},
    {"No.": 6, "Dimension": "ADAPTABILITY", "Definition": "Flexibility and ability to improvise under changing conditions"},
    {"No.": 7, "Dimension": "COMMUNITY", "Definition": "Willingness to help others and accept help during emergencies"},
    {"No.": 8, "Dimension": "PREPAREDNESS", "Definition": "Level of awareness and planning for a mass evacuation"}
])

decisions, players = load_data()
questions, options, authority_info = load_questions_and_options()
decisions, players, expected_question_count = prepare_complete_responses(decisions, players, questions)

# ===========================
# MUNICIPALITY FILTER
# ===========================
st.title("Player Behavior Dashboard")

col_title, col_filter = st.columns([3, 1])
with col_filter:
    available_service_areas = sorted(COUNTY_TO_MUNICIPALITIES.keys())
    if players['wellbeing_services_county'].eq('Unmapped municipalities').any():
        available_service_areas.append('Unmapped municipalities')

    counties = ["All"] + available_service_areas
    selected_county = st.selectbox(
        "Filter by Wellbeing Services County or Special Area:",
        counties,
        key="county_filter"
    )

    county_filtered_players = players
    if selected_county != "All":
        county_filtered_players = players[players["wellbeing_services_county"] == selected_county]

    if selected_county == 'All':
        municipalities = sorted({
            municipality
            for county_municipalities in COUNTY_TO_MUNICIPALITIES.values()
            for municipality in county_municipalities
        } | set(players['municipality'].dropna().tolist()))
    elif selected_county in COUNTY_TO_MUNICIPALITIES:
        municipalities = sorted(COUNTY_TO_MUNICIPALITIES[selected_county])
    else:
        municipalities = sorted(county_filtered_players['municipality'].dropna().unique().tolist())

    municipalities = ["All"] + municipalities
    selected_municipality = st.selectbox(
        "Filter by Municipality:",
        municipalities,
        key="municipality_filter"
    )

# Filter data based on selected county and municipality
filtered_players = county_filtered_players
if selected_municipality != "All":
    filtered_players = county_filtered_players[county_filtered_players["municipality"] == selected_municipality]

if filtered_players.empty:
    if selected_municipality != 'All':
        st.info(f"No data available for {selected_municipality}.")
    else:
        st.info(f"No data available for {selected_county}.")
    st.stop()

filtered_players_ids = filtered_players["id"].tolist()
decisions = decisions[decisions["player_id"].isin(filtered_players_ids)]
players = filtered_players

# Group by player_id and question_id, then pivot
decisions_pivot = decisions.pivot_table(
    index='player_id',
    columns='question_id',
    values='option_chosen',
    aggfunc='first'  # In case of duplicates, take first
).reset_index()

# Rename columns to Q1, Q2, Q3, Q4, Q5 based on position
decisions_pivot = decisions_pivot.rename(columns={col: f"Q{i+1}" for i, col in enumerate(decisions_pivot.columns[1:])})

# Get dimension scores (sum across all responses per player)
dimension_cols = ['score_react', 'score_trust', 'score_indep', 'score_adapt', 'score_mobil', 'score_safety', 'score_commu', 'score_prep']
scores_per_player = decisions.groupby('player_id')[dimension_cols].sum().reset_index()

# Calculate personality (dominant dimension) for each player
scores_per_player['Personality'] = scores_per_player[dimension_cols].idxmax(axis=1).map(SCORE_COLUMN_TO_PERSONALITY)
scores_per_player['PersonalityType'] = scores_per_player['Personality'].map(PERSONALITY_MAPPING)

# Merge decisions with player info
players_rename = players.rename(columns={
    'id': 'player_id',
    'nickname': 'User',
    'gender': 'Gender',
    'municipality': 'Municipality',
    'has_children': 'Has Children',
    'has_elderly': 'Has Elderly',
    'has_pets': 'Has Pets',
    'has_evacuation_experience': 'Has Evacuation Experience',
    'wellbeing_services_county': SERVICE_AREA_LABEL
})
data = decisions_pivot.merge(scores_per_player, on='player_id', how='left')
data = data.merge(
    players_rename[[
        'player_id', 'User', 'age', 'Gender', 'Municipality',
        'Has Children', 'Has Elderly', 'Has Pets', 'Has Evacuation Experience', SERVICE_AREA_LABEL
    ]],
    on='player_id',
    how='left'
)
data = data.rename(columns={'age': 'Age'})

# Prepare dimension scores with updated column names
dim_scores = data[['score_react', 'score_trust', 'score_indep', 'score_adapt', 'score_mobil', 'score_safety', 'score_commu', 'score_prep']].copy()
dim_scores.columns = ['REACT', 'TRUST', 'INDEPENDENT', 'ADAPTABILITY', 'MOBILITY', 'SAFETY', 'COMMUNITY', 'PREPAREDNESS']
dim_scores["PersonalityType"] = data["PersonalityType"].values

tab1, tab2, tab3, tab4 = st.tabs([
    "Personality Overview",
    "Player Profile",
    "Response Patterns",
    "Behavioral Insights"
])

# -----------------------------
# Row 0: User Profile Information
# -----------------------------
with tab1:
    st.header("Personality Overview")
    with st.container(border=True):
        st.markdown("**About this tab**")
        st.write("This tab shows the personality test result. It contains an overview of the players' personality types and their distribution.")
    
    col1, col2 = st.columns([1, 2])

    with col1.container(border=True, height="stretch"):
        st.subheader("Personality Overview")
        st.metric("Total Players", len(data))
        st.metric("Most Common Personality", data["PersonalityType"].mode()[0])

    with col2.container(border=True, height="stretch"):
        st.subheader("Personality Distribution")
        personality_counts = data["PersonalityType"].value_counts().reset_index()
        personality_counts.columns = ["Personality", "Count"]

        # Create pie chart
        fig = px.pie(personality_counts, names="Personality", values="Count", hole=0.4)

        # Update layout for fonts
        fig.update_layout(
            legend=dict(
                title=dict(text="Personality Type", font=dict(size=16)),  # Legend title font
                font=dict(size=16),                                  # Legend items font size
            )
        )

        # Optional: increase the font size for slice labels (inside the pie)
        fig.update_traces(
            textfont_size=16,   # Font size for text on pie slices
            hoverlabel=dict(font_size=16)  # Font size for hover info
        )

        # Display
        st.plotly_chart(fig, width='stretch')

# -----------------------------
# Row 1
# -----------------------------
with tab2:
    st.header("Player Profile")
    with st.container(border=True):
        st.markdown("**About this tab**")
        st.write("This tab shows the profile information of players, including their demographics, municipality, household information, and previous evacuation experience. The municipality map highlights where the players are located, while the municipality player rate chart compares the number of players in each municipality with its population size, helping you see where response is relatively active or inactive.")

    col_u1, col_u2 = st.columns([2,2])

    # --- Player Municipality Map and Response Rate ---
    st.markdown("\n")
    st.markdown("---")
    col_map, col_rate = st.columns([2, 1])
    with col_map:
        st.subheader("Player Municipality Map")
        muni_counts_map = data["Municipality"].value_counts().reset_index()
        muni_counts_map.columns = ["Municipality", "Count"]
        muni_counts_map["lat"] = muni_counts_map["Municipality"].map(lambda x: municipality_data.get(x, {}).get("lat", None))
        muni_counts_map["lon"] = muni_counts_map["Municipality"].map(lambda x: municipality_data.get(x, {}).get("lon", None))
        muni_counts_map = muni_counts_map.dropna(subset=["lat", "lon"])
        if not muni_counts_map.empty:
            fig_map = px.scatter_mapbox(
                muni_counts_map,
                lat="lat",
                lon="lon",
                size="Count",
                hover_name="Municipality",
                hover_data={"Count": True},
                size_max=30,
                zoom=5,
                height=400
            )
            fig_map.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0},
                showlegend=False
            )
            st.plotly_chart(fig_map, width='stretch', key="muni_map")
        else:
            st.info("No municipality coordinates available for mapping.")
    with col_rate:
        st.subheader("Municipality Player Rate")
        muni_counts = data["Municipality"].value_counts().reset_index()
        muni_counts.columns = ["Municipality", "Players"]
        muni_counts["Population"] = muni_counts["Municipality"].map(lambda x: municipality_data.get(x, {}).get("population", None))
        muni_counts = muni_counts.dropna(subset=["Population"])
        muni_counts["Player Rate (%)"] = 100 * muni_counts["Players"] / muni_counts["Population"]
        muni_counts = muni_counts.sort_values(by="Player Rate (%)", ascending=True)
        fig_muni = px.bar(
            muni_counts,
            x="Player Rate (%)",
            y="Municipality",
            orientation="h",
            color_discrete_sequence=["#6589CC"]
        )
        fig_muni.update_layout(
            xaxis_title="<b>Player Rate (%)</b>",
            yaxis_title="<b>Municipality</b>",
            yaxis=dict(tickfont=dict(size=12)),
            xaxis=dict(tickfont=dict(size=12))
        )
        st.plotly_chart(fig_muni, width='stretch', key="muni_rate")

    # --- Age Distribution ---
    with col_u1.container(border=True, height="stretch"):
        st.subheader("Age Distribution")

        # Create age bins (adjust range if needed)
        bins = list(range(0, 101, 10))  # 0-10, 10-20, ..., 90-100
        labels = [f"{i}-{i+10}" for i in bins[:-1]]

        data["Age_Group"] = pd.cut(data["Age"], bins=bins, labels=labels, right=False)

        # Count per group
        age_counts = data["Age_Group"].value_counts().sort_index().reset_index()
        age_counts.columns = ["Age Group", "Count"]

        # Plot
        fig_age = px.bar(
            age_counts,
            x="Age Group",
            y="Count",
            color_discrete_sequence=["#F59F4A"]  # <-- orange color
        )

        fig_age.update_layout(
            xaxis_title="<b>Age Group</b>",
            yaxis_title="<b>Count</b>",
            xaxis=dict(tickfont=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12))
        )

        st.plotly_chart(fig_age, width='stretch', key="age_dist")

    # --- Gender Distribution ---
    with col_u2.container(border=True, height="stretch"):
        st.subheader("Gender Distribution")

        gender_counts = data["Gender"].value_counts().reset_index()
        gender_counts.columns = ["Gender", "Count"]
        gender_counts["Gender"] = gender_counts["Gender"].fillna("Unknown").astype(str).str.title()

        # Define color mapping
        color_map = {
            "Male": "#6bc0fd",
            "Female": "#ff8aa6",
            "Other": "#d5d5d5",
            "Unknown": "#d5d5d5"
        }

        fig_gender = px.pie(
            gender_counts,
            names="Gender",
            values="Count",
            color="Gender",
            color_discrete_map=color_map
        )

        st.plotly_chart(fig_gender, width='stretch', key="gender_dist")

    st.markdown("\n")
    col_children, col_elderly, col_pets, col_evacuation = st.columns(4)

    # --- Household Status Distribution ---
    with col_children.container(border=True, height="stretch"):
        st.subheader("Children in Household")
        children_counts = summarize_boolean_feature(data, "Has Children", "Has Children")
        fig_children = px.pie(
            children_counts,
            names="Has Children",
            values="Count",
            color="Has Children",
            category_orders={"Has Children": ["Yes", "No"]},
            color_discrete_map={"Yes": "#6FA8DC", "No": "#D9E2F3"},
            hole=0.45
        )
        fig_children.update_layout(showlegend=True)
        st.plotly_chart(fig_children, width='stretch', key="children_dist")

    with col_elderly.container(border=True, height="stretch"):
        st.subheader("Elderly in Household")
        elderly_counts = summarize_boolean_feature(data, "Has Elderly", "Has Elderly")
        fig_elderly = px.pie(
            elderly_counts,
            names="Has Elderly",
            values="Count",
            color="Has Elderly",
            category_orders={"Has Elderly": ["Yes", "No"]},
            color_discrete_map={"Yes": "#F4A261", "No": "#FCE1CC"},
            hole=0.45
        )
        fig_elderly.update_layout(showlegend=True)
        st.plotly_chart(fig_elderly, width='stretch', key="elderly_dist")

    with col_pets.container(border=True, height="stretch"):
        st.subheader("Pets in Household")
        pets_counts = summarize_boolean_feature(data, "Has Pets", "Has Pets")
        fig_pets = px.pie(
            pets_counts,
            names="Has Pets",
            values="Count",
            color="Has Pets",
            category_orders={"Has Pets": ["Yes", "No"]},
            color_discrete_map={"Yes": "#7BC47F", "No": "#DCEFD9"},
            hole=0.45
        )
        fig_pets.update_layout(showlegend=True)
        st.plotly_chart(fig_pets, width='stretch', key="pets_dist")

    with col_evacuation.container(border=True, height="stretch"):
        st.subheader("Evacuation Experience")
        evacuation_counts = summarize_boolean_feature(data, "Has Evacuation Experience", "Has Evacuation Experience")
        fig_evacuation = px.pie(
            evacuation_counts,
            names="Has Evacuation Experience",
            values="Count",
            color="Has Evacuation Experience",
            category_orders={"Has Evacuation Experience": ["Yes", "No"]},
            color_discrete_map={"Yes": "#B38DDB", "No": "#E7DDF6"},
            hole=0.45
        )
        fig_evacuation.update_layout(showlegend=True)
        st.plotly_chart(fig_evacuation, width='stretch', key="evacuation_dist")




        
# -----------------------------
# Row 2
# -----------------------------
with tab3:
    st.header("Response Patterns")
    with st.container(border=True):
        st.markdown("**About this tab**")
        st.write("This tab shows the answer distribution question by question. Read each question card together with its response chart, then use the hover details to inspect which behavioral dimensions each answer option measures.")

    with st.container(border=True):
        st.subheader("Dimension Definitions")
        st.dataframe(DIMENSION_DEFINITIONS, width='stretch', hide_index=True)

    # Define color map for answers
    color_map = {
        'A': '#65b0e4',  # blue
        'B': '#ffa250',  # orange
        'C': '#5dd25d',  # green
        'D': '#e36364',  # red
        'E': '#aa87cb',  # purple
        'F': "#E9E50D"   # yellow
    }
    
    dimension_cols_short = ['react', 'trust', 'indep', 'adapt', 'mobil', 'safety', 'commu', 'prep']
    dimension_names = ['REACT', 'TRUST', 'INDEPENDENT', 'ADAPTABILITY', 'MOBILITY', 'SAFETY', 'COMMUNITY', 'PREPAREDNESS']
    dimension_weight_columns = {
        dim_short: f'weight_{dim_short}'
        for dim_short in dimension_cols_short
    }
    
    # Sort questions by order_index
    questions_sorted = questions.sort_values('order_index')
    
    for _, q_row in questions_sorted.iterrows():
        question_id = q_row['id']
        question_text = q_row['question_text']
        order_idx = q_row['order_index']
        authority_row = authority_info[authority_info['id'] == order_idx]
        authority_note = None if authority_row.empty else authority_row['authority_info'].iloc[0]
        
        # Get option texts for labels
        q_options = options[options['question_id'] == question_id].copy()
        q_options_dict = dict(zip(q_options['option_key'], q_options['option_text']))
        measured_dimensions = [
            dim_name
            for dim_short, dim_name in zip(dimension_cols_short, dimension_names)
            if dimension_weight_columns[dim_short] in q_options.columns
            and q_options[dimension_weight_columns[dim_short]].fillna(0).ne(0).any()
        ]
        measured_dimension_text = ", ".join(measured_dimensions) if measured_dimensions else "No scored dimensions"
        
        # Get responses for this question from decisions data
        q_decisions = decisions[decisions['question_id'] == question_id]
        all_options = sorted(q_options['option_key'].unique())
        
        with st.container(border=True):
            col_overview, col_chart = st.columns([1.15, 1])
            with col_overview.container(border=True):
                st.subheader(f"Question {order_idx} | {measured_dimension_text}")
                st.write(question_text)
                st.markdown("**Answer Options:**")
                for opt_key in all_options:
                    opt_text = q_options_dict.get(opt_key, '')
                    if pd.notna(opt_text):
                        opt_text_str = str(opt_text).strip()
                    else:
                        opt_text_str = ''

                    if opt_text_str:
                        st.markdown(f"- **{opt_key}**: {opt_text_str}")
                    else:
                        st.markdown(f"- **{opt_key}**: Other")
                if pd.notna(authority_note):
                    st.markdown("***Authority Focus***")
                    st.markdown(f"_{str(authority_note)}_")
                else:
                    st.markdown("***Authority Focus***")
                    st.markdown("_No authority guidance is available for this question yet._")

            with col_chart.container(border=True):
                st.subheader("Answer Distribution")

                answer_counts = q_decisions['option_chosen'].value_counts().reset_index()
                answer_counts.columns = ['Option', 'Count']
                answer_counts = answer_counts.set_index('Option').reindex(all_options, fill_value=0).reset_index()
                answer_counts['Count'] = answer_counts['Count'].astype(int)
                answer_counts['Option_Text'] = answer_counts['Option'].map(
                    lambda x: f"{x}: {q_options_dict.get(x, 'N/A')}"
                )
                answer_counts['BarColor'] = answer_counts['Option'].map(color_map).fillna('#999999')
                for dim_short, dim_name in zip(dimension_cols_short, dimension_names):
                    weight_column = dimension_weight_columns[dim_short]
                    option_weights = q_options.set_index('option_key')[weight_column] if weight_column in q_options.columns else pd.Series(dtype=float)
                    answer_counts[dim_name] = answer_counts['Option'].map(option_weights).fillna(0).astype(int)

                hover_dimension_fields = {
                    dimension_name: True
                    for dimension_name in measured_dimensions
                }

                fig_answer = px.bar(
                    answer_counts,
                    x='Option',
                    y='Count',
                    hover_data={
                        'Count': True,
                        'Option_Text': False,
                        **hover_dimension_fields
                    },
                    hover_name='Option_Text',
                    category_orders={'Option': all_options}
                )

                fig_answer.update_traces(
                    marker_color=answer_counts['BarColor'],
                    width=0.55
                )
                fig_answer.update_layout(
                    xaxis_title="<b>Answer Option</b>",
                    yaxis_title="<b>Number of Responses</b>",
                    xaxis=dict(
                        tickfont=dict(size=12),
                        type='category',
                        tickangle=0,
                        categoryorder='array',
                        categoryarray=all_options
                    ),
                    yaxis=dict(tickfont=dict(size=12), tickformat='d'),
                    showlegend=False,
                    hovermode='x unified',
                    bargap=0.35
                )

                st.plotly_chart(fig_answer, width='stretch')

        st.markdown("---")

# -----------------------------
# Row 3
# -----------------------------
with tab4:
    st.header("Behavioral Insights")
    with st.container(border=True):
        st.markdown("**About this tab**")
        st.write("This tab helps you interpret the behavioral structure behind the responses rather than single answers alone. Use it to compare dimensions, spot clustering patterns, and identify where scores differ across places, age groups, and personality profiles.")
    
    
    dimension_names = ['REACT', 'TRUST', 'INDEPENDENT', 'ADAPTABILITY', 'MOBILITY', 'SAFETY', 'COMMUNITY', 'PREPAREDNESS']
    score_columns = ['score_react', 'score_trust', 'score_indep', 'score_adapt', 'score_mobil', 'score_safety', 'score_commu', 'score_prep']
    score_column_to_dimension = dict(zip(score_columns, dimension_names))
    
    col_dimension_heatmap, col_geo_compare = st.columns(2)

    with col_dimension_heatmap.container(border=True, height="stretch"):
        st.subheader("Dimension Heatmap")
        st.caption("Use this chart to see which dimensions tend to increase or decrease together. Values closer to 1 indicate strong positive relationships, while values closer to -1 indicate trade-offs between dimensions.")

        # Compute correlation
        corr = dim_scores.drop(columns=["PersonalityType"]).corr()

        fig_heatmap = px.imshow(
            corr,
            text_auto=".2f",             # show numbers rounded to 2 decimals
            color_continuous_scale='RdBu_r',
            aspect="auto",
            color_continuous_midpoint=0
        )

        fig_heatmap.update_layout(
            xaxis_title="Dimension",
            yaxis_title="Dimension",
            xaxis=dict(tickfont=dict(size=15)),
            yaxis=dict(tickfont=dict(size=15)),
            coloraxis_colorbar=dict(title="Correlation", tickfont=dict(size=12))
        )

        st.plotly_chart(fig_heatmap, width='stretch')
        
    with col_geo_compare.container(border=True, height="stretch"):
        geographic_field = SERVICE_AREA_LABEL if selected_county == "All" else "Municipality"
        geographic_label = "Service Area" if selected_county == "All" else "Municipality"
        st.subheader(f"Average Dimension by {geographic_label}")
        st.caption(f"Use this chart to compare the average dimension profile across {geographic_label.lower()}s. Higher bars indicate dimensions that are more prominent on average in that place.")

        geographic_scores = data[[geographic_field] + score_columns].rename(columns=score_column_to_dimension)
        geographic_scores = geographic_scores.groupby(geographic_field)[dimension_names].mean().reset_index()

        if len(geographic_scores) > 1:
            geographic_scores_long = geographic_scores.melt(
                id_vars=[geographic_field],
                value_vars=dimension_names,
                var_name="Dimension",
                value_name="Average Score"
            )
            fig_geo_compare = px.bar(
                geographic_scores_long,
                x="Dimension",
                y="Average Score",
                color=geographic_field,
                barmode="group"
            )
            fig_geo_compare.update_layout(
                xaxis_title="<b>Dimension</b>",
                yaxis_title="<b>Average Player Score</b>",
                legend_title_text=geographic_label
            )
            st.plotly_chart(fig_geo_compare, width='stretch')
        else:
            st.info(f"At least two {geographic_label.lower()}s are needed to compare average dimension scores.")
    st.markdown("\n")

    col_dimension_spider, col_dimension_boxplot = st.columns(2)

    with col_dimension_spider.container(border=True, height="stretch"):
        st.subheader("Dimension Spider Chart")
        st.caption("Use this chart to read the overall balance of average scores across all eight dimensions. The farther a point is from the center, the more strongly that dimension is.")

        avg_scores = dim_scores.drop(columns=["PersonalityType"]).mean().reset_index()
        avg_scores.columns = ["Dimension", "Score"]

        fig_radar = px.line_polar(avg_scores, r="Score", theta="Dimension", line_close=True)
        fig_radar.update_traces(fill='toself')
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    range=[-3, 3],
                    tickvals=[-3, -2, -1, 0, 1, 2, 3]
                )
            )
        )

        st.plotly_chart(fig_radar, width='stretch')

    with col_dimension_boxplot.container(border=True):
        st.subheader("Dimension Score Distributions")
        st.caption("Use this chart to inspect spread and variability rather than averages only. Wider distributions and distant points indicate dimensions where players differ more from one another.")
        distribution_scores = dim_scores.drop(columns=["PersonalityType"]).melt(
            var_name="Dimension",
            value_name="Score"
        )
        fig_distribution = px.box(
            distribution_scores,
            x="Dimension",
            y="Score",
            color="Dimension",
            points="all"
        )
        fig_distribution.update_layout(
            xaxis_title="<b>Dimension</b>",
            yaxis_title="<b>Player Score</b>",
            showlegend=False
        )
        st.plotly_chart(fig_distribution, width='stretch')

    st.markdown("\n")


    col_demo_heatmap, col_scatter = st.columns(2)

    with col_demo_heatmap.container(border=True, height="stretch"):
        st.subheader("Personality by Age Group")
        st.caption("Use this chart to see which personality types appear more often in different age groups. Darker cells indicate combinations with more players.")
        demographic_data = data.copy()
        age_bins = list(range(0, 101, 10))
        age_labels = [f"{value}-{value+10}" for value in age_bins[:-1]]
        demographic_data["Age Group"] = pd.cut(
            demographic_data["Age"],
            bins=age_bins,
            labels=age_labels,
            right=False
        )
        personality_age_counts = demographic_data.groupby(
            ["PersonalityType", "Age Group"],
            observed=False
        ).size().reset_index(name="Count")
        personality_age_pivot = personality_age_counts.pivot(
            index="PersonalityType",
            columns="Age Group",
            values="Count"
        ).fillna(0)
        fig_personality_heatmap = px.imshow(
            personality_age_pivot,
            text_auto=True,
            color_continuous_scale="Sunsetdark",
            aspect="auto"
        )
        fig_personality_heatmap.update_layout(
            xaxis_title="<b>Age Group</b>",
            yaxis_title="<b>Personality Type</b>",
            coloraxis_colorbar=dict(title="Players")
        )
        st.plotly_chart(fig_personality_heatmap, width='stretch')

    
    with col_scatter.container(border=True, height="stretch"):
        st.subheader("Personality Dimension Pair Scatter")
        st.caption("Use this chart to compare two dimensions at the player level and look for clusters, outliers, or trade-offs. Points that group together suggest players with similar behaviors on those two dimensions.")
        scatter_col1, scatter_col2 = st.columns(2)
        with scatter_col1:
            scatter_x = st.selectbox(
                "X Dimension",
                dimension_names,
                index=0,
                key="dimension_scatter_x"
            )
        with scatter_col2:
            scatter_y_options = [dimension for dimension in dimension_names if dimension != scatter_x]
            default_y_index = 1 if len(scatter_y_options) > 1 else 0
            scatter_y = st.selectbox(
                "Y Dimension",
                scatter_y_options,
                index=default_y_index,
                key="dimension_scatter_y"
            )

        scatter_data = dim_scores.copy()
        scatter_data["User"] = data["User"].values
        fig_scatter = px.scatter(
            scatter_data,
            x=scatter_x,
            y=scatter_y,
            color="PersonalityType",
            hover_name="User"
        )
        fig_scatter.update_layout(
            xaxis_title=f"<b>{scatter_x}</b>",
            yaxis_title=f"<b>{scatter_y}</b>"
        )
        st.plotly_chart(fig_scatter, width='stretch')

    st.markdown("\n")
    col_flow, col_rate_map = st.columns(2)