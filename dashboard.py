import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(layout="wide")

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
    """Load data from secrets or local files"""
    try:
        # Try to load from Streamlit secrets (for Streamlit Cloud deployment)
        decisions_csv = st.secrets["decisions_data"]
        players_csv = st.secrets["players_data"]
        
        decisions = pd.read_csv(StringIO(decisions_csv))
        players = pd.read_csv(StringIO(players_csv))
    except (FileNotFoundError, KeyError):
        # Fallback to local files (for local development)
        decisions = pd.read_csv("data/feedback_round1/decisions_rows.csv")
        players = pd.read_csv("data/feedback_round1/players_rows.csv")
    
    return decisions, players

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

# Transform decisions data: pivot to get one row per player with Q1-Q5 answers
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

st.title("Player Behavior Dashboard")

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

    # col3, col4 = st.columns(2)
    col3, col4 = st.columns([3,2])

    # Define a color map for all possible answers
    color_map = {
        'A': '#65b0e4',  # blue
        'B': '#ffa250',  # orange
        'C': '#5dd25d',  # green
        'D': '#e36364',  # red
        'E': '#aa87cb'   # purple (for questions with 5 answers)
    }

    with col3.container(border=True, height="stretch"):
        st.subheader("Question Answer Distribution")

        questions = [f"Q{i}" for i in range(1, 6)]
        # Count responses for each answer per question
        stack_df = data[questions].apply(lambda x: x.value_counts()).fillna(0).T

        legend_order = ['A', 'B', 'C', 'D', 'E']  # Include all possible answers

        fig_stack = go.Figure()

        # Loop through all answers present in the data
        for ans in stack_df.columns:
            fig_stack.add_bar(
                y=stack_df.index,
                x=stack_df[ans],
                name=ans,
                orientation='h',
                marker_color=color_map.get(ans, '#7f7f7f')  # fallback gray if missing
            )

        fig_stack.update_layout(
            barmode='stack',
            xaxis_title="Response Count",
            yaxis_title="Question",
            legend_title="Answer",
            legend=dict(font=dict(size=20)),
            legend_traceorder="normal",  # Keep the order as added
            xaxis=dict(tickfont=dict(size=15)),
            yaxis=dict(tickfont=dict(size=15))
        )

        st.plotly_chart(fig_stack, use_container_width=True)



    with col4.container(border=True, height="stretch"):
        st.subheader("Out-of-the-Box Answers")

        # Combine all free-text responses into one string (from decisions table)
        text_data = " ".join(
            decisions['other_text']
            .fillna("")              # remove NaNs
            .astype(str)             # ensure all are strings
            .values
        ).strip()

        # Generate word cloud only if there is text data
        if text_data and len(text_data.split()) > 0:
            wc = WordCloud(
                width=800,
                height=600,
                background_color="white",
                colormap="inferno",
                max_words=200
            ).generate(text_data)

            # Display with matplotlib
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.info("No free-text responses available")

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
            color_continuous_scale='Oranges',
            aspect="auto"
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