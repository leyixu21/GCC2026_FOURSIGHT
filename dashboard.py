import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data():
    responses = pd.read_csv("data/responses.csv")
    personalities = pd.read_csv("data/personalities.csv")

    score_tables = {}
    for i in range(1, 6):
        score_tables[f"Q{i}"] = pd.read_csv(f"data/Q{i}_scores.csv")
    return responses, personalities, score_tables

responses, personalities, score_tables = load_data()

responses["User"] = responses["User"].astype(str).str.strip()
personalities["User"] = personalities["User"].astype(str).str.strip()

data = responses.merge(personalities, on="User", how="left")

# -----------------------------
# Compute Dimension Scores
# -----------------------------

def compute_dimension_scores(responses, score_tables):
    dimensions = ["REACT", "TRUST", "INDEPEND", "ADAPT", "MOBILITY", "SAFETY"]
    user_scores = []

    for _, row in responses.iterrows():
        total = dict.fromkeys(dimensions, 0)
        for q in score_tables.keys():
            answer = row[q]
            table = score_tables[q]
            match = table[table["Answer"] == answer]

            if not match.empty:
                for dim in dimensions:
                    val = match.iloc[0][dim]
                    if pd.notna(val):
                        total[dim] += val

        user_scores.append(total)

    return pd.DataFrame(user_scores)

base_responses = data[[f"Q{i}" for i in range(1, 6)]]
dim_scores = compute_dimension_scores(base_responses, score_tables)
dim_scores["Personality"] = data["Personality"].values

st.title("Citizen Behavior Dashboard")

# -----------------------------
# Row 1
# -----------------------------
col1, col2 = st.columns([1, 2])

with col1.container(border=True, height="stretch"):
    st.subheader("Overview")
    st.metric("Total Respondents", len(data))
    st.metric("Most Common Personality", data["Personality"].mode()[0])

with col2.container(border=True, height="stretch"):
    st.subheader("Personality Distribution")
    personality_counts = data["Personality"].value_counts().reset_index()
    personality_counts.columns = ["Personality", "Count"]

    # Create pie chart
    fig = px.pie(personality_counts, names="Personality", values="Count", hole=0.4)

    # Update layout for fonts
    fig.update_layout(
        legend=dict(
            title=dict(text="Personality", font=dict(size=16)),  # Legend title font
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
# Row 2
# -----------------------------
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
    st.subheader("Dimension Spider Chart")

    avg_scores = dim_scores.drop(columns=["Personality"]).mean().reset_index()
    avg_scores.columns = ["Dimension", "Score"]

    fig_radar = px.line_polar(avg_scores, r="Score", theta="Dimension", line_close=True)
    fig_radar.update_traces(fill='toself')

    st.plotly_chart(fig_radar, use_container_width=True)


# -----------------------------
# Row 3
# -----------------------------
col5, col6 = st.columns(2)

with col5.container(border=True, height="stretch"):
    st.subheader("Dimension Heatmap")

    # Compute correlation
    corr = dim_scores.drop(columns=["Personality"]).corr()

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

    st.subheader("Out-of-the-Box Answers")

    # Combine all free-text columns into one string
    free_text_cols = [f"Q{i}_text" for i in range(1, 6)]
    text_data = " ".join(
        data[free_text_cols]
        .fillna("")              # remove NaNs
        .astype(str)             # ensure all are strings
        .values.flatten()        # flatten into 1D array
    )

    # Generate word cloud
    wc = WordCloud(
        width=800,
        height=400,
        background_color="white",
        colormap="inferno",
        max_words=200
    ).generate(text_data)

    # Display with matplotlib
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)