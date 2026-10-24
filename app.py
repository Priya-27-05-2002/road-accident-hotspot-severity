from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

# -------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------
st.set_page_config(
    page_title="Great Britain Road Accident Explorer",
    page_icon="🚦",
    layout="wide"
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
DOCS = ROOT / "documentation"


st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Project overview metric cards */
div[data-testid="stMetric"] {
    background-color: #EAF2F8 !important;
    border: 1px solid #C8D9E8 !important;
    padding: 18px 16px !important;
    border-radius: 12px !important;
}

/* Metric labels */
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] label {
    color: #34495E !important;
    font-weight: 600 !important;
}

/* Metric values/numbers */
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div,
div[data-testid="stMetricValue"] > div {
    color: #12304A !important;
    font-weight: 800 !important;
}

/* Metric delta text, if displayed */
div[data-testid="stMetricDelta"] {
    color: #12304A !important;
}
</style>
""", unsafe_allow_html=True)


st.title("🚦 Great Britain Road Accident Explorer")
st.caption(
    "Spatiotemporal hotspot screening and severity analysis | 2021–2025"
)

# -------------------------------------------------------
# LOAD DATA SAFELY
# -------------------------------------------------------
@st.cache_data
def load_csv(filename):
    path = DATA / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

yearly = load_csv("accident_counts_by_year.csv")
monthly = load_csv("accident_counts_by_month.csv")
hourly = load_csv("accident_counts_by_hour.csv")
authority = load_csv("accident_counts_by_authority.csv")
categories = load_csv("grid_hotspot_temporal_category_summary.csv")
grid_year = load_csv("grid_accident_counts_by_year_5km.csv")
grid_temporal = load_csv("grid_hotspot_temporal_comparison_2021_2025.csv")

results_path = DOCS / "phase9_final_results_table.csv"
results = pd.read_csv(results_path) if results_path.exists() else pd.DataFrame()

recall_path = DOCS / "phase9_class_wise_recall.csv"
recall = pd.read_csv(recall_path) if recall_path.exists() else pd.DataFrame()

# -------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------
st.sidebar.header("Dashboard filters")

available_years = []
if not yearly.empty and "year" in yearly.columns:
    available_years = sorted(
        pd.to_numeric(yearly["year"], errors="coerce")
        .dropna().astype(int).unique().tolist()
    )

if not available_years and not grid_year.empty and "year" in grid_year.columns:
    available_years = sorted(
        pd.to_numeric(grid_year["year"], errors="coerce")
        .dropna().astype(int).unique().tolist()
    )

selected_year = st.sidebar.selectbox(
    "Select year",
    available_years,
    index=len(available_years) - 1 if available_years else 0
) if available_years else None

top_n = st.sidebar.slider(
    "Number of local authorities to show",
    min_value=5,
    max_value=30,
    value=10,
    step=5
)

st.sidebar.info(
    "The grid results are high-count screening results, "
    "not statistically confirmed hotspots."
)

# -------------------------------------------------------
# KPI CARDS
# -------------------------------------------------------
st.header("Project overview")

total_inside = 513252
occupied_cells = 7615
high_count_records = 1566
persistent_cells = 257

if not results.empty and {"metric", "value"}.issubset(results.columns):
    result_lookup = dict(zip(results["metric"].astype(str), results["value"]))
    # Display the project-wide validated metrics above. Avoid depending
    # on inconsistent result-table labels.

c1, c2, c3, c4 = st.columns(4)
c1.metric("Collisions inside GB", f"{total_inside:,}")
c2.metric("Occupied 5 km grid cells", f"{occupied_cells:,}")
c3.metric("High-count grid-year records", f"{high_count_records:,}")
c4.metric("Persistent cells", f"{persistent_cells:,}")

st.caption(
    "Project-wide summary counts. Counts refer to different processing "
    "stages; they should not be treated as interchangeable."
)

# -------------------------------------------------------
# TABS
# -------------------------------------------------------
tab_overview, tab_time, tab_hotspots, tab_authority, tab_model = st.tabs([
    "Overview", "Time analysis", "Hotspots", "Local authorities",
    "Severity model"
])

with tab_overview:
    st.subheader("Final project maps")

    map1 = FIGURES / "phase9_final_accident_concentration_2021_2025.png"
    map2 = FIGURES / "phase9_final_temporal_hotspot_categories_2021_2025.png"
    map3 = FIGURES / "phase9_final_high_count_screen_2025.png"

    left, right = st.columns(2)
    with left:
        if map1.exists():
            st.image(str(map1), caption="Accident concentration, 2021–2025",
                     use_container_width=True)
        else:
            st.warning("Accident concentration map not found.")
    with right:
        if map2.exists():
            st.image(str(map2), caption="Temporal hotspot categories",
                     use_container_width=True)
        else:
            st.warning("Temporal hotspot map not found.")

    if map3.exists():
        st.image(str(map3), caption="High-count grid screening for 2025",
                 use_container_width=True)

    st.warning(
        "A high observed count does not by itself establish statistical "
        "significance, risk, or causation."
    )

with tab_time:
    st.subheader("Temporal accident patterns")

    if not yearly.empty and "year" in yearly.columns:
        st.markdown("**Annual collision counts**")
        ydf = yearly.copy()
        ydf["year"] = pd.to_numeric(ydf["year"], errors="coerce")
        numeric_cols = [
            c for c in ydf.columns
            if c != "year" and pd.api.types.is_numeric_dtype(ydf[c])
        ]
        if numeric_cols:
            count_col = numeric_cols[0]
            st.plotly_chart(
                px.line(
                    ydf.sort_values("year"), x="year", y=count_col,
                    markers=True, title="Collisions by year"
                ),
                use_container_width=True
            )
        else:
            st.dataframe(ydf, use_container_width=True)
    else:
        st.info("Annual summary CSV is missing or has an unexpected schema.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Monthly pattern**")
        if not monthly.empty:
            st.plotly_chart(
                px.line(monthly, x=monthly.columns[0],
                        y=monthly.columns[-1], markers=True),
                use_container_width=True
            )
        else:
            st.info("Monthly summary unavailable.")

    with col2:
        st.markdown("**Hourly pattern**")
        if not hourly.empty:
            st.plotly_chart(
                px.bar(hourly, x=hourly.columns[0], y=hourly.columns[-1]),
                use_container_width=True
            )
        else:
            st.info("Hourly summary unavailable.")

    if selected_year is not None and not grid_year.empty:
        st.markdown(f"**5 km grid-year records — {selected_year}**")
        if "year" in grid_year.columns:
            filtered = grid_year[
                pd.to_numeric(grid_year["year"], errors="coerce")
                == selected_year
            ]
            st.metric("Grid-year records", f"{len(filtered):,}")
            st.dataframe(filtered.head(100), use_container_width=True)
            st.caption("Showing at most 100 rows of the selected year's grid data.")

with tab_hotspots:
    st.subheader("Temporal hotspot screening")

    if not categories.empty:
        category_col = "temporal_category" if "temporal_category" in categories.columns else categories.columns[0]
        value_candidates = [
            c for c in categories.columns
            if c != category_col and pd.api.types.is_numeric_dtype(categories[c])
        ]
        if value_candidates:
            value_col = value_candidates[0]
            st.plotly_chart(
                px.bar(
                    categories, x=category_col, y=value_col,
                    color=category_col,
                    title="Grid cells by temporal category"
                ),
                use_container_width=True
            )
            st.dataframe(categories, use_container_width=True)
        else:
            st.dataframe(categories, use_container_width=True)
    else:
        st.info("Hotspot category summary unavailable.")

    if not grid_temporal.empty:
        st.markdown("**Temporal comparison table**")
        st.dataframe(grid_temporal.head(200), use_container_width=True)
        st.caption("First 200 grid cells shown to keep the dashboard responsive.")

with tab_authority:
    st.subheader("Local-authority summary")

    if not authority.empty:
        name_candidates = [
            c for c in authority.columns
            if any(word in c.lower() for word in ["authority", "name", "lad", "area"])
        ]
        metric_candidates = [
            c for c in authority.columns
            if c not in name_candidates
            and pd.api.types.is_numeric_dtype(authority[c])
        ]

        if metric_candidates:
            metric_col = st.selectbox(
                "Select statistic",
                metric_candidates,
                key="authority_metric"
            )
            display_df = authority.sort_values(
                metric_col, ascending=False
            ).head(top_n)

            name_col = name_candidates[0] if name_candidates else authority.columns[0]
            st.plotly_chart(
                px.bar(
                    display_df.sort_values(metric_col),
                    x=metric_col, y=name_col, orientation="h",
                    title=f"Top {top_n} local authorities"
                ),
                use_container_width=True
            )
            st.dataframe(display_df, use_container_width=True)
        else:
            st.dataframe(authority.head(top_n), use_container_width=True)
    else:
        st.info("Local-authority summary unavailable.")

with tab_model:
    st.subheader("Severity classification performance")

    st.markdown(
        "**Selected main model: Class-Weighted Random Forest**  \\n"
        "Selected because it achieved the highest macro F1 among the four "
        "models evaluated on the chronological 2025 test set."
    )

    comparison_path = DOCS / "phase6_model_comparison.csv"

    if comparison_path.exists():
        comparison = pd.read_csv(comparison_path)

        st.markdown("**Comparison of all evaluated models**")
        st.dataframe(
            comparison.round(4),
            use_container_width=True,
            hide_index=True
        )

        selected = comparison[
            comparison["Model"] == "Class-Weighted Random Forest"
        ]

        if not selected.empty:
            row = selected.iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("Accuracy", f"{row['Accuracy']:.4f}")
            col2.metric("Macro F1", f"{row['Macro F1']:.4f}")
            col3.metric("Weighted F1", f"{row['Weighted F1']:.4f}")

    st.markdown("**Class-wise recall — Class-Weighted Random Forest**")
    rf_recall = pd.DataFrame({
        "Severity": ["Fatal", "Serious", "Slight"],
        "Recall": [0.5877, 0.2485, 0.5904]
    })
    st.dataframe(rf_recall, use_container_width=True, hide_index=True)

    st.markdown(
        "**Interpretation:** Class-Weighted Random Forest has the highest "
        "macro F1 (0.3371) among the four tested models. However, "
        "Class-Weighted Logistic Regression performs better on Fatal recall "
        "(0.6146 versus 0.5877) and Serious recall "
        "(0.2968 versus 0.2485). The Random Forest is retained as the main "
        "model to align with the base paper, not because it is best on every "
        "metric."
    )

    st.warning(
        "Fatal-class precision is low, so some collisions predicted as Fatal "
        "are not Fatal in the recorded labels. These predictions are for "
        "research and should not be used alone for operational decisions."
    )

# -------------------------------------------------------
# FOOTER
# -------------------------------------------------------
st.divider()
st.caption(
    "Research dashboard | Source: UK Department for Transport STATS19 "
    "collision data and project-generated spatial summaries. "
    "Use the methodology and limitations report when interpreting results."
)
