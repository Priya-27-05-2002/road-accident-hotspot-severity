
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


# -------------------------------------------------------
# GLOBAL STYLING
# -------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .custom-metric {
        background-color: #EAF2F8;
        border: 1px solid #C8D9E8;
        border-radius: 12px;
        padding: 18px 14px;
        min-height: 115px;
        box-sizing: border-box;
    }

    .custom-metric-label {
        color: #172B4D !important;
        font-size: 14px;
        font-weight: 700;
        line-height: 1.5;
        margin-bottom: 10px;
    }

    .custom-metric-value {
        color: #12304A !important;
        font-size: 28px;
        font-weight: 800;
        line-height: 1.3;
        overflow-wrap: anywhere;
    }

    div[data-testid="stMetric"] {
        background-color: #EAF2F8;
        border: 1px solid #C8D9E8;
        padding: 14px;
        border-radius: 10px;
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p {
        color: #172B4D !important;
        opacity: 1 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #12304A !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------------------------------------
# PAGE TITLE
# -------------------------------------------------------
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

    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.warning(f"Could not read {filename}: {exc}")
        return pd.DataFrame()


yearly = load_csv("accident_counts_by_year.csv")
monthly = load_csv("accident_counts_by_month.csv")
hourly = load_csv("accident_counts_by_hour.csv")
authority = load_csv("accident_counts_by_authority.csv")
categories = load_csv("grid_hotspot_temporal_category_summary.csv")
grid_year = load_csv("grid_accident_counts_by_year_5km.csv")
grid_temporal = load_csv(
    "grid_hotspot_temporal_comparison_2021_2025.csv"
)

results_path = DOCS / "phase9_final_results_table.csv"
results = (
    pd.read_csv(results_path)
    if results_path.exists()
    else pd.DataFrame()
)

recall_path = DOCS / "phase9_class_wise_recall.csv"
recall = (
    pd.read_csv(recall_path)
    if recall_path.exists()
    else pd.DataFrame()
)


# -------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------
st.sidebar.header("Dashboard filters")

available_years = []

if not yearly.empty and "year" in yearly.columns:
    available_years = sorted(
        pd.to_numeric(yearly["year"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

if not available_years and not grid_year.empty:
    if "year" in grid_year.columns:
        available_years = sorted(
            pd.to_numeric(grid_year["year"], errors="coerce")
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )

selected_year = None

if available_years:
    default_index = len(available_years) - 1

    selected_year = st.sidebar.selectbox(
        "Select year",
        available_years,
        index=default_index
    )

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

# Project-wide summary values
total_inside = 513252
occupied_cells = 7615
high_count_records = 1566
persistent_cells = 257

# The results table is loaded for reference, but the displayed
# project-wide figures above remain the configured summary values.
if not results.empty and {"metric", "value"}.issubset(results.columns):
    result_lookup = dict(
        zip(results["metric"].astype(str), results["value"])
    )

metric_cards = [
    ("Collisions inside GB", f"{total_inside:,}"),
    ("Occupied 5 km grid cells", f"{occupied_cells:,}"),
    ("High-count grid-year records", f"{high_count_records:,}"),
    ("Persistent cells", f"{persistent_cells:,}")
]

columns = st.columns(4)

for col, (heading, number) in zip(columns, metric_cards):
    with col:
        st.markdown(
            f"""
            <div class="custom-metric">
                <div class="custom-metric-label">{heading}</div>
                <div class="custom-metric-value">{number}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.caption(
    "Project-wide summary counts. Counts refer to different processing "
    "stages; they should not be treated as interchangeable."
)


# -------------------------------------------------------
# DASHBOARD TABS
# -------------------------------------------------------
tab_overview, tab_time, tab_hotspots, tab_authority, tab_model = st.tabs(
    [
        "Overview",
        "Time analysis",
        "Hotspots",
        "Local authorities",
        "Severity model"
    ]
)


# -------------------------------------------------------
# TAB 1: OVERVIEW
# -------------------------------------------------------
with tab_overview:
    st.subheader("Final project maps")

    map1 = (
        FIGURES /
        "phase9_final_accident_concentration_2021_2025.png"
    )
    map2 = (
        FIGURES /
        "phase9_final_temporal_hotspot_categories_2021_2025.png"
    )
    map3 = (
        FIGURES /
        "phase9_final_high_count_screen_2025.png"
    )

    left, right = st.columns(2)

    with left:
        if map1.exists():
            st.image(
                str(map1),
                caption="Accident concentration, 2021–2025",
                use_container_width=True
            )
        else:
            st.warning(
                "Accident concentration map not found. "
                "Check outputs/figures and the expected filename."
            )

    with right:
        if map2.exists():
            st.image(
                str(map2),
                caption="Temporal hotspot categories",
                use_container_width=True
            )
        else:
            st.warning(
                "Temporal hotspot map not found. "
                "Check outputs/figures and the expected filename."
            )

    if map3.exists():
        st.image(
            str(map3),
            caption="High-count grid screening for 2025",
            use_container_width=True
        )
    else:
        st.warning(
            "The 2025 high-count screening map was not found."
        )

    st.warning(
        "A high observed count does not by itself establish statistical "
        "significance, risk, or causation."
    )


# -------------------------------------------------------
# TAB 2: TIME ANALYSIS
# -------------------------------------------------------
with tab_time:
    st.subheader("Temporal accident patterns")

    # Annual collision counts
    if not yearly.empty and "year" in yearly.columns:
        st.markdown("**Annual collision counts**")

        ydf = yearly.copy()
        ydf["year"] = pd.to_numeric(
            ydf["year"],
            errors="coerce"
        )
        ydf = ydf.dropna(subset=["year"])

        numeric_cols = [
            column
            for column in ydf.columns
            if column != "year"
            and pd.api.types.is_numeric_dtype(ydf[column])
        ]

        if numeric_cols:
            count_col = numeric_cols[0]

            st.plotly_chart(
                px.line(
                    ydf.sort_values("year"),
                    x="year",
                    y=count_col,
                    markers=True,
                    title="Collisions by year"
                ),
                use_container_width=True
            )
        else:
            st.dataframe(
                ydf,
                use_container_width=True
            )
    else:
        st.info(
            "Annual summary CSV is missing or has an unexpected schema."
        )

    # Monthly and hourly patterns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Monthly pattern**")

        if not monthly.empty and len(monthly.columns) >= 2:
            st.plotly_chart(
                px.line(
                    monthly,
                    x=monthly.columns[0],
                    y=monthly.columns[-1],
                    markers=True,
                    title="Collisions by month"
                ),
                use_container_width=True
            )
        else:
            st.info("Monthly summary unavailable.")

    with col2:
        st.markdown("**Hourly pattern**")

        if not hourly.empty and len(hourly.columns) >= 2:
            st.plotly_chart(
                px.bar(
                    hourly,
                    x=hourly.columns[0],
                    y=hourly.columns[-1],
                    title="Collisions by hour"
                ),
                use_container_width=True
            )
        else:
            st.info("Hourly summary unavailable.")

    # Selected year's grid-year records
    st.divider()
    st.subheader("5 km grid-year records")

    if selected_year is None:
        st.info(
            "A year cannot be selected because no year values "
            "were found in the available summary data."
        )

    elif grid_year.empty:
        st.info(
            "Grid-year data is unavailable. Check "
            "data/processed/grid_accident_counts_by_year_5km.csv."
        )

    elif "year" not in grid_year.columns:
        st.warning(
            "The grid-year CSV does not contain a 'year' column."
        )

    else:
        # Convert year values safely before filtering
        grid_year_copy = grid_year.copy()
        grid_year_copy["year"] = pd.to_numeric(
            grid_year_copy["year"],
            errors="coerce"
        )

        filtered = grid_year_copy[
            grid_year_copy["year"] == selected_year
        ].copy()

        st.markdown(
            f"**Records for {selected_year}**"
        )

        # Custom card: heading and number are displayed together
        st.markdown(
            f"""
            <div class="custom-metric">
                <div class="custom-metric-label">
                    Grid-year records for {selected_year}
                </div>
                <div class="custom-metric-value">
                    {len(filtered):,}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        if not filtered.empty:
            st.dataframe(
                filtered.head(100),
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Showing at most 100 rows of the selected year's "
                "grid data. The metric above counts all matching rows."
            )
        else:
            st.info(
                f"No grid-year records were found for {selected_year}."
            )


# -------------------------------------------------------
# TAB 3: HOTSPOTS
# -------------------------------------------------------
with tab_hotspots:
    st.subheader("Temporal hotspot screening")

    if not categories.empty:
        category_col = (
            "temporal_category"
            if "temporal_category" in categories.columns
            else categories.columns[0]
        )

        value_candidates = [
            column
            for column in categories.columns
            if column != category_col
            and pd.api.types.is_numeric_dtype(categories[column])
        ]

        if value_candidates:
            value_col = value_candidates[0]

            st.plotly_chart(
                px.bar(
                    categories,
                    x=category_col,
                    y=value_col,
                    color=category_col,
                    title="Grid cells by temporal category"
                ),
                use_container_width=True
            )

            st.dataframe(
                categories,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(
                categories,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Hotspot category summary unavailable.")

    if not grid_temporal.empty:
        st.markdown("**Temporal comparison table**")

        st.dataframe(
            grid_temporal.head(200),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "First 200 grid cells shown to keep the dashboard responsive."
        )
    else:
        st.info(
            "Temporal comparison data is unavailable."
        )


# -------------------------------------------------------
# TAB 4: LOCAL AUTHORITIES
# -------------------------------------------------------
with tab_authority:
    st.subheader("Local-authority summary")

    if not authority.empty:
        name_candidates = [
            column
            for column in authority.columns
            if any(
                word in column.lower()
                for word in [
                    "authority",
                    "name",
                    "lad",
                    "area"
                ]
            )
        ]

        metric_candidates = [
            column
            for column in authority.columns
            if column not in name_candidates
            and pd.api.types.is_numeric_dtype(authority[column])
        ]

        if metric_candidates:
            metric_col = st.selectbox(
                "Select statistic",
                metric_candidates,
                key="authority_metric"
            )

            display_df = authority.sort_values(
                metric_col,
                ascending=False
            ).head(top_n)

            name_col = (
                name_candidates[0]
                if name_candidates
                else authority.columns[0]
            )

            st.plotly_chart(
                px.bar(
                    display_df.sort_values(metric_col),
                    x=metric_col,
                    y=name_col,
                    orientation="h",
                    title=f"Top {top_n} local authorities"
                ),
                use_container_width=True
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(
                authority.head(top_n),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Local-authority summary unavailable.")


# -------------------------------------------------------
# TAB 5: SEVERITY MODEL
# -------------------------------------------------------
with tab_model:
    st.subheader("Severity classification performance")

    st.markdown(
        "**Selected main model: Class-Weighted Random Forest**  \n"
        "It was selected because it achieved the highest macro F1 "
        "among the four models evaluated on the chronological 2025 test set."
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

        if "Model" in comparison.columns:
            selected = comparison[
                comparison["Model"]
                == "Class-Weighted Random Forest"
            ]

            if not selected.empty:
                row = selected.iloc[0]

                col1, col2, col3 = st.columns(3)

                if "Accuracy" in comparison.columns:
                    col1.metric(
                        "Accuracy",
                        f"{row['Accuracy']:.4f}"
                    )

                if "Macro F1" in comparison.columns:
                    col2.metric(
                        "Macro F1",
                        f"{row['Macro F1']:.4f}"
                    )

                if "Weighted F1" in comparison.columns:
                    col3.metric(
                        "Weighted F1",
                        f"{row['Weighted F1']:.4f}"
                    )
    else:
        st.info(
            "Model comparison file not found: "
            "documentation/phase6_model_comparison.csv"
        )

    st.markdown(
        "**Class-wise recall — Class-Weighted Random Forest**"
    )

    rf_recall = pd.DataFrame(
        {
            "Severity": ["Fatal", "Serious", "Slight"],
            "Recall": [0.5877, 0.2485, 0.5904]
        }
    )

    st.dataframe(
        rf_recall,
        use_container_width=True,
        hide_index=True
    )

    st.markdown(
        "**Interpretation:** Class-Weighted Random Forest has the highest "
        "macro F1 (0.3371) among the four tested models. However, "
        "Class-Weighted Logistic Regression performs better on Fatal recall "
        "(0.6146 versus 0.5877) and Serious recall "
        "(0.2968 versus 0.2485). The Random Forest is retained as the main "
        "model to align with the base paper, not because it is best on "
        "every metric."
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
