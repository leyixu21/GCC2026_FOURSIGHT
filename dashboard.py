import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import StringIO
import gdown
import os
import tempfile

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
        auth_password = "authority2026"  # Change this to your preferred password
    
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
    'REACT': 'The Quickstarter',
    'TRUST': 'The Guided Follower',
    'INDEPENDENT': 'The Independent Thinker',
    'ADAPT': 'The Flexible Adapter',
    'MOBILITY': 'The Go-Getter',
    'SAFETY': 'The Safety Seeker'
}

# Reverse mapping for reference
DIMENSION_TO_PERSONALITY = {
    'score_react': ('REACT', 'The Quickstarter'),
    'score_trust': ('TRUST', 'The Guided Follower'),
    'score_indep': ('INDEPENDENT', 'The Independent Thinker'),
    'score_adapt': ('ADAPT', 'The Flexible Adapter'),
    'score_mobil': ('MOBILITY', 'The Go-Getter'),
    'score_safety': ('SAFETY', 'The Safety Seeker')
}

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data():
    """Load data from Google Drive or local files"""
    # Google Drive file IDs
    DECISIONS_ID = "1CAH-4YQGR7Wjz_iFXNCgbWdin-Lr55h-"
    PLAYERS_ID = "1IPhAbKp40hYUuo32x6Oyn9lSnDesBtsS"
    
    try:
        # Try to download from Google Drive
        with tempfile.TemporaryDirectory() as tmpdir:
            decisions_path = os.path.join(tmpdir, "decisions_rows.csv")
            players_path = os.path.join(tmpdir, "players_rows.csv")
            
            def download_from_gdrive(file_id, output_name):
                url = f'https://drive.google.com/uc?id={file_id}'
                gdown.download(url, output_name, quiet=True)
            
            download_from_gdrive(DECISIONS_ID, decisions_path)
            download_from_gdrive(PLAYERS_ID, players_path)
            
            decisions = pd.read_csv(decisions_path)
            players = pd.read_csv(players_path)
    except Exception as e:
        # Fallback to local files
        st.warning(f"Could not load from Google Drive: {e}. Using local files...")
        decisions = pd.read_csv("data/feedback_round1/decisions_rows.csv")
        players = pd.read_csv("data/feedback_round1/players_rows.csv")
    
    return decisions, players

@st.cache_data
def load_questions_and_options():
    """Load questions and options reference data from Google Drive or local files"""
    # Google Drive file IDs
    QUESTIONS_ID = "11-pbVsGkjH5dbJbpuj5-7LzBZibY8auJ"
    OPTIONS_ID = "1YIVOEORl__jN5Jbc-hGbhu_TScdtv4sY"
    
    def download_from_gdrive(file_id, output_name):
        url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(url, output_name, quiet=True)
    
    try:
        # Try to download from Google Drive
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = os.path.join(tmpdir, "questions_rows.csv")
            options_path = os.path.join(tmpdir, "options_rows.csv")
            
            download_from_gdrive(QUESTIONS_ID, questions_path)
            download_from_gdrive(OPTIONS_ID, options_path)
            
            questions = pd.read_csv(questions_path)
            options = pd.read_csv(options_path)
    except Exception as e:
        # Fallback to local files
        st.warning(f"Could not load from Google Drive: {e}. Using local files...")
        questions = pd.read_csv("data/feedback_round1/questions_rows.csv")
        options = pd.read_csv("data/feedback_round1/options_rows.csv")
    
    return questions, options

@st.cache_data
def calculate_personality(dimension_scores):
    """
    Calculate dominant personality from dimension scores.
    Returns the dimension name with the highest average score.
    In case of ties, uses the first occurrence (deterministic).
    """
    if len(dimension_scores) == 0:
        return None
    max_score = dimension_scores.max()
    return dimension_scores.idxmax()

decisions, players = load_data()
questions, options = load_questions_and_options()

# ===========================
# MUNICIPALITY FILTER
# ===========================
st.title("Player Behavior Dashboard")

col_title, col_filter = st.columns([3, 1])
with col_filter:
    municipalities = ["All"] + sorted(players["municipality"].unique().tolist())
    selected_municipality = st.selectbox(
        "Filter by Municipality:",
        municipalities,
        key="municipality_filter"
    )

# Filter data based on selected municipality
if selected_municipality != "All":
    filtered_players_ids = players[players["municipality"] == selected_municipality]["id"].tolist()
    decisions = decisions[decisions["player_id"].isin(filtered_players_ids)]
    players = players[players["municipality"] == selected_municipality]

# Group by player_id and question_id, then pivot
decisions_pivot = decisions.pivot_table(
    index='player_id',
    columns='question_id',
    values='option_chosen',
    aggfunc='first'  # In case of duplicates, take first
).reset_index()

# Rename columns to Q1, Q2, Q3, Q4, Q5 based on position
decisions_pivot = decisions_pivot.rename(columns={col: f"Q{i+1}" for i, col in enumerate(decisions_pivot.columns[1:])})

# Get dimension scores (average across all responses per player)
dimension_cols = ['score_react', 'score_trust', 'score_indep', 'score_adapt', 'score_mobil', 'score_safety']
scores_per_player = decisions.groupby('player_id')[dimension_cols].mean().reset_index()

# Calculate personality (dominant dimension) for each player
dim_names = ['REACT', 'TRUST', 'INDEPENDENT', 'ADAPT', 'MOBILITY', 'SAFETY']
personalities = []
personality_titles = []
for idx, row in scores_per_player.iterrows():
    dim_scores = row[dimension_cols]
    personality = calculate_personality(dim_scores)
    # Map dimension keys to personality names
    personality_map = {
        'score_react': 'REACT',
        'score_trust': 'TRUST',
        'score_indep': 'INDEPENDENT',
        'score_adapt': 'ADAPT',
        'score_mobil': 'MOBILITY',
        'score_safety': 'SAFETY'
    }
    personality_label = personality_map.get(personality, 'UNKNOWN')
    personalities.append(personality_label)
    personality_titles.append(PERSONALITY_MAPPING.get(personality_label, personality_label))

scores_per_player['Personality'] = personalities
scores_per_player['PersonalityType'] = personality_titles

# Merge decisions with player info
players_rename = players.rename(columns={'id': 'player_id', 'nickname': 'User', 'gender': 'Gender', 'municipality': 'Municipality'})
data = decisions_pivot.merge(scores_per_player, on='player_id', how='left')
data = data.merge(players_rename[['player_id', 'User', 'age', 'Gender', 'Municipality']], on='player_id', how='left')
data = data.rename(columns={'age': 'Age'})

# Prepare dimension scores with updated column names
base_responses = data[[f"Q{i}" for i in range(1, 6)]]
dim_scores = data[['score_react', 'score_trust', 'score_indep', 'score_adapt', 'score_mobil', 'score_safety']].copy()
dim_scores.columns = ['REACT', 'TRUST', 'INDEPENDENT', 'ADAPT', 'MOBILITY', 'SAFETY']
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
    
    col1, col2 = st.columns([1, 2])

    with col1.container(border=True, height="stretch"):
        st.subheader("Personality Overview")
        st.metric("Total Respondents", len(data))
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
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Row 1
# -----------------------------
with tab2:
    st.header("Player Profile")

    col_u1, col_u2, col_u3 = st.columns(3)

    # Age Distribution
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
            color_discrete_sequence=["#F5B270"]  # <-- orange color
        )

        fig_age.update_layout(
            xaxis_title="<b>Age Group</b>",
            yaxis_title="<b>Count</b>",
            xaxis=dict(tickfont=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12))
        )

        st.plotly_chart(fig_age, use_container_width=True)

    # Gender Distribution
    with col_u2.container(border=True, height="stretch"):
        st.subheader("Gender Distribution")

        gender_counts = data["Gender"].value_counts().reset_index()
        gender_counts.columns = ["Gender", "Count"]

        # Define color mapping
        color_map = {
            "Male": "#a2d2f4",
            "Female": "#eca5b5",
            "Others": "#d5d5d5"
        }

        fig_gender = px.pie(
            gender_counts,
            names="Gender",
            values="Count",
            color="Gender",
            color_discrete_map=color_map
        )

        st.plotly_chart(fig_gender, use_container_width=True)

    # Municipality Distribution
    with col_u3.container(border=True, height="stretch"):
        st.subheader("Municipality Distribution")

        muni_counts = data["Municipality"].value_counts().head(10).reset_index()
        muni_counts.columns = ["Municipality", "Count"]

        # Reverse order for horizontal bar (largest on top)
        muni_counts = muni_counts.sort_values(by="Count", ascending=True)

        fig_muni = px.bar(
            muni_counts,
            x="Count",
            y="Municipality",
            orientation="h",
            color_discrete_sequence=["#7BD082"]  # orange theme
        )

        fig_muni.update_layout(
            xaxis_title="<b>Count</b>",
            yaxis_title="<b>Municipality</b>",
            yaxis=dict(tickfont=dict(size=12)),
            xaxis=dict(tickfont=dict(size=12))
        )

        st.plotly_chart(fig_muni, use_container_width=True)
        
# -----------------------------
# Row 2
# -----------------------------
with tab3:
    st.header("Response Patterns")
    
    # Define color map for answers
    color_map = {
        'A': '#65b0e4',  # blue
        'B': '#ffa250',  # orange
        'C': '#5dd25d',  # green
        'D': '#e36364',  # red
        'E': '#aa87cb'   # purple
    }
    
    dimension_cols_short = ['react', 'trust', 'indep', 'adapt', 'mobil', 'safety']
    dimension_names = ['REACT', 'TRUST', 'INDEPENDENT', 'ADAPT', 'MOBILITY', 'SAFETY']
    
    # Sort questions by order_index
    questions_sorted = questions.sort_values('order_index')
    
    for _, q_row in questions_sorted.iterrows():
        question_id = q_row['id']
        question_text = q_row['question_text']
        order_idx = q_row['order_index']
        
        # Get option texts for labels
        q_options = options[options['question_id'] == question_id].copy()
        q_options_dict = dict(zip(q_options['option_key'], q_options['option_text']))
        
        # Get responses for this question from decisions data
        q_decisions = decisions[decisions['question_id'] == question_id]
        all_options = sorted(q_options['option_key'].unique())
        
        # Create 2x2 grid layout
        col_left, col_right = st.columns([1, 1])
        
        # ============ ROW 1 (TOP) ============
        # LEFT (ROW 1): Question & Answer Options Panel
        with col_left.container(border=True):
            st.markdown(f"### Question {order_idx}")
            st.write(question_text)
            
            st.markdown("**Answer Options:**")
            for opt_key in all_options:
                opt_text = q_options_dict.get(opt_key, '')
                # Handle NaN and empty values - show "Other" for placeholder options
                if pd.notna(opt_text):
                    opt_text_str = str(opt_text).strip()
                else:
                    opt_text_str = ''
                
                if opt_text_str:
                    st.markdown(f"- **{opt_key}**: {opt_text_str}")
                else:
                    # Show "Other" for options without text
                    st.markdown(f"- **{opt_key}**: Other")
        
        # RIGHT (ROW 1): Dimension Scores Table
        with col_right.container(border=True):
            st.subheader("Dimension Scores")
            
            # Create dimension scores table for each option
            dimension_data = []
            
            for opt_key in all_options:
                opt_row = q_options[q_options['option_key'] == opt_key]
                if not opt_row.empty:
                    dimension_values = []
                    for dim_col in dimension_cols_short:
                        col_name = f'weight_{dim_col}'
                        if col_name in opt_row.columns:
                            dimension_values.append(int(opt_row[col_name].values[0]))
                        else:
                            dimension_values.append(0)
                    
                    # Add row to table data
                    row_dict = {'Option': opt_key}
                    for i, dim_name in enumerate(dimension_names):
                        row_dict[dim_name] = dimension_values[i]
                    dimension_data.append(row_dict)
            
            if dimension_data:
                df_dimensions = pd.DataFrame(dimension_data)
                
                # Display as interactive table
                st.dataframe(
                    df_dimensions.set_index('Option'),
                    use_container_width=True,
                    height=200
                )
        
        # ============ ROW 2 (BOTTOM) ============
        # LEFT (ROW 2): Answer Distribution Chart
        with col_left.container(border=True):
            st.subheader("Answer Distribution")
            
            # Count responses for this question
            answer_counts = q_decisions['option_chosen'].value_counts().reset_index()
            answer_counts.columns = ['Option', 'Count']
            
            # Ensure all possible options are shown, even with 0 counts
            answer_counts = answer_counts.set_index('Option').reindex(all_options, fill_value=0).reset_index()
            answer_counts['Count'] = answer_counts['Count'].astype(int)
            
            # Add full text to answer_counts
            answer_counts['Option_Text'] = answer_counts['Option'].map(
                lambda x: f"{x}: {q_options_dict.get(x, 'N/A')}"
            )
            
            # Create bar chart with category order
            fig_answer = px.bar(
                answer_counts,
                x='Option',
                y='Count',
                color='Option',
                color_discrete_map=color_map,
                hover_data={'Option_Text': False},
                hover_name='Option_Text',
                category_orders={'Option': all_options}
            )
            
            fig_answer.update_layout(
                xaxis_title="<b>Answer Option</b>",
                yaxis_title="<b>Number of Responses</b>",
                xaxis=dict(tickfont=dict(size=12), type='category', tickangle=0),
                yaxis=dict(tickfont=dict(size=12), tickformat='d'),
                showlegend=False,
                hovermode='x unified',
                bargap=0.2
            )
            
            st.plotly_chart(fig_answer, use_container_width=True)
        
        # RIGHT (ROW 2): Custom Responses Word Cloud
        with col_right.container(border=True):
            st.subheader("Custom Responses")
            
            # Get free-text responses for this question
            q_decisions_with_text = q_decisions[q_decisions['is_other'] == True]
            text_data = " ".join(
                q_decisions_with_text['other_text']
                .fillna("")
                .astype(str)
                .values
            ).strip()
            
            if text_data and len(text_data.split()) > 0:
                wc = WordCloud(
                    width=400,
                    height=300,
                    background_color="white",
                    colormap="inferno",
                    max_words=100
                ).generate(text_data)
                
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("No custom responses")
        
        st.divider()

# -----------------------------
# Row 3
# -----------------------------
with tab4:
    st.header("Behavioral Insights")
    col5, col6 = st.columns(2)

    with col5.container(border=True, height="stretch"):
        st.subheader("Dimension Heatmap")

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

        st.plotly_chart(fig_heatmap, use_container_width=True)

    with col6.container(border=True, height="stretch"):
        st.subheader("Dimension Spider Chart")

        avg_scores = dim_scores.drop(columns=["PersonalityType"]).mean().reset_index()
        avg_scores.columns = ["Dimension", "Score"]

        fig_radar = px.line_polar(avg_scores, r="Score", theta="Dimension", line_close=True)
        fig_radar.update_traces(fill='toself')

        st.plotly_chart(fig_radar, use_container_width=True)