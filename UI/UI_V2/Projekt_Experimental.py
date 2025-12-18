import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu
import sklearn.preprocessing as skp
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import WhiteKernel,RBF,Matern, RationalQuadratic
import gpytorch 
import torch 
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
import numpy as np
from sklearn.model_selection import train_test_split


# --------------------------
# Page Config and CSS
# --------------------------
st.set_page_config(
    page_title="Lake Water Quality Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>

/* =========================================================
   MULTISELECT — TAG PILLS
   ========================================================= */
div[data-baseweb="select"] span[data-baseweb="tag"] {
    background-color: #4dabf7 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
    font-weight: 600 !important;
}

/* X icon inside pill */
div[data-baseweb="select"] span[data-baseweb="tag"] svg {
    fill: #ffffff !important;
}

/* =========================================================
   MULTISELECT — INPUT BOX
   ========================================================= */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1px solid #4dabf7 !important;
    border-radius: 6px !important;
}

/* Text inside input box */
div[data-baseweb="select"] > div div {
    color: #003f5c !important;
    font-weight: 500 !important;
}

/* =========================================================
   MULTISELECT — DROPDOWN OPTIONS
   ========================================================= */
div[data-baseweb="select"] ul li {
    color: #003f5c !important;
    background-color: #ffffff !important;
    font-size: 14px !important;
}

/* Hover effect for options */
div[data-baseweb="select"] ul li:hover {
    background-color: #70c1b3 !important;
    color: #ffffff !important;
}

/* =========================================================
   TABS
   ========================================================= */
.stTabs [data-baseweb="tab"] {
    color: #003f5c !important;
    font-weight: 500 !important;
}

/* Selected tab text */
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #4dabf7 !important;
    font-weight: 600 !important;
}

/* Selected tab underline */
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #4dabf7 !important;
}

/* =========================================================
   NUMBER INPUT — PLUS/MINUS BUTTONS
   ========================================================= */
div.stNumberInput button {
    background-color: white !important;  /* Blue background */
    color: black !important;               /* White + and - signs */
    border: none !important;
    border-radius: 4px !important;
}

/* Hover effect */
div.stNumberInput button:hover {
    background-color:  #4dabf7  !important;
}

/* Active/pressed effect */
div.stNumberInput button:active {
    background-color: #003f7f !important;
}

/* Slider styling reverted to default */


</style>
""", unsafe_allow_html=True)


# sidebar nav (simple)
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Upload", "Predict", "Help"],
        icons=["house", "cloud-upload", "graph-up", "patch-question"],
        default_index=1, styles={
            "container": {"padding": "0!important", "background-color": "#d0ebf7"},
            "icon": {"color": "#003f5c", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "color": "#003f5c", "margin": "0px"},
            "nav-link-selected": {"background-color": "#4dabf7", "color": "white"},
        }
    )
# app title
st.title("💧 Lake Water 3D Quality Dashboard")

# home page (just a short intro)
if selected == "Home":
    st.markdown(
        """
        Welcome to the **Lake Water Quality Dashboard**!
        Use the **Upload** page to start analyzing your lake dataset.
        """
    )

# upload page (bring your csv here)
elif selected == "Upload":
    st.subheader("Upload your lake CSV dataset")
    uploaded = st.file_uploader("", type="csv")

    # if a new file is added, use it
    if uploaded is not None:
        data = pd.read_csv(uploaded)
        st.session_state["data"] = data
    # otherwise keep the last one so you dont lose work
    elif "data" in st.session_state:
        data = st.session_state["data"]
    else:
        st.info("Upload a CSV file to begin...")
        st.stop()

    # quick check for the must-have columns
    required = {"latitude", "longitude", "depth"}
    if not required.issubset(data.columns):
        st.error(f"Your file must include: {required}")
        st.stop()
    
    # check if timestamp column exists and parse it
    if "timestamp" not in data.columns:
        st.warning("⚠️ No 'timestamp' column found. For temporal predictions, add a 'timestamp' column to your CSV.")
        st.info("Proceeding without temporal features...")
        has_month = False
    else:
        try:
            # parse timestamp and extract month and year
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['month'] = data['timestamp'].dt.month
            data['year'] = data['timestamp'].dt.year
            
            # create combined month_year identifier for grouping
            data['month_year'] = data['year'].astype(str) + '-' + data['month'].astype(str).str.zfill(2)
            
            unique_periods = data['month_year'].nunique()
            has_month = True
            st.success(f"✅ Temporal data detected: {unique_periods} unique month-year periods in dataset")
            st.info(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
        except Exception as e:
            st.error(f"Error parsing timestamp column: {e}")
            st.info("Proceeding without temporal features...")
            has_month = False

    # drop gps points with too few sats (less reliable)
    if "num_sats" in data.columns:
        before = len(data)
        data = data[data["num_sats"] >= 4].reset_index(drop=True)
        removed = before - len(data)
        if removed > 0:
            st.info(f"Removed {removed} unreliable points (num_sats < 4).")

    # convert lat/lon to simple cartesian x/y for plotting
    lat = np.deg2rad(data["latitude"])
    lon = np.deg2rad(data["longitude"])
    R = 6371000
    data["x"] = R * np.cos(lat) * np.cos(lon)
    data["y"] = R * np.cos(lat) * np.sin(lon)
    st.session_state["data"]=data
    st.session_state["has_month"] = has_month
    # sidebar filters & display opts
    st.sidebar.header("Controls")
    exclude_cols = {"latitude", "longitude", "x", "y", "num_sats", "depth",'depth_inverted','depth_bin','month','year','month_year','timestamp'}

    numeric_cols = [c for c in data.columns if c not in exclude_cols]

    selected_features = st.sidebar.multiselect(
        "Select measurements to summarize:", numeric_cols, default=numeric_cols)

    bin_width = st.sidebar.number_input(
        "Depth bin width (m):", min_value=0.1, max_value=10.0, value=1.0, step=0.1
    )

    color_option = st.sidebar.selectbox(
        "Color 3D plot by:", options=numeric_cols + [None], index=len(numeric_cols)-1
    )
    
    # Month-year filter for 3D plot (if temporal data exists)
    if has_month and data['month_year'].nunique() > 1:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🗓️ Temporal Filter**")
        available_periods = sorted(data['month_year'].unique())
        
        show_all_periods = st.sidebar.checkbox("Show all periods", value=True)
        
        if not show_all_periods:
            selected_period = st.sidebar.selectbox(
                "Select period to display:",
                options=available_periods,
                format_func=lambda x: pd.to_datetime(x + '-01').strftime('%B %Y')
            )
        else:
            selected_period = None
    else:
        selected_period = None

    # main tabs
    tab1, tab2, tab3 = st.tabs(["3D Plot", "Statistics", "Raw Data"])

    # 3d scatter (regular depth, not inverted)
    with tab1:
        st.markdown("### 3D Measurement Positions")
        
        # Filter data by period if selected
        if selected_period is not None:
            plot_data = data[data['month_year'] == selected_period].copy()
            period_label = pd.to_datetime(selected_period + '-01').strftime('%B %Y')
            st.info(f"🗓️ Showing data for **{period_label}** - {len(plot_data)} measurements")
        else:
            plot_data = data.copy()
            if has_month and data['month_year'].nunique() > 1:
                st.info(f"📊 Showing all periods ({data['month_year'].nunique()} periods, {len(plot_data)} total measurements)")

        fig = px.scatter_3d(
            plot_data,
            x="x",
            y="y",
            z="depth",
            color=color_option,
            title=f"3D Positions colored by {color_option}" if color_option else "3D Positions",
            hover_data=numeric_cols,
            color_continuous_scale="Viridis",
        )
        fig.update_traces(marker=dict(size=5))
        fig.update_layout(
            paper_bgcolor="#f0f4f8",
            scene=dict(
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                zaxis_title="Depth (m)",
                zaxis=dict(autorange='reversed')
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # stats per depth
    with tab2:
        if selected_features:
            # Check if temporal data exists
            has_temporal = has_month and data['month'].nunique() > 1
            
            if has_temporal:
                # Show tabs for depth vs temporal statistics
                stats_tab1, stats_tab2, stats_tab3 = st.tabs(["📊 By Depth", "🗓️ By Month", "🔀 Depth × Month"])
            else:
                # Just depth statistics
                stats_tab1 = st.container()
            
            # === DEPTH STATISTICS ===
            with stats_tab1:
                depth_min = data["depth"].min()
                depth_max = data["depth"].max()
                bins = np.arange(depth_min, depth_max + bin_width, bin_width)
                labels = [
                    f"{round(b, 1)}-{round(b+bin_width, 1)} m" for b in bins[:-1]]
                data["depth_bin"] = pd.cut(
                    data["depth"], bins=bins, labels=labels, include_lowest=True)

                stats = data.groupby("depth_bin")[selected_features].agg(
                    ["mean", "std", "min", "median", "max", "count"])
                
                # little summary cards up top, just for at-a-glance
                st.markdown("### 📊 Overall Dataset Summary")
                metric_cols = st.columns(len(selected_features))
                for idx, feature in enumerate(selected_features):
                    with metric_cols[idx]:
                        mean_val = data[feature].mean()
                        std_val = data[feature].std()
                        min_val = data[feature].min()
                        max_val = data[feature].max()
                        
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    padding: 20px; border-radius: 10px; color: white; text-align: center;
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                            <h4 style='margin:0; font-size:14px; font-weight:600;'>{feature.upper()}</h4>
                            <p style='margin:10px 0 5px 0; font-size:28px; font-weight:700;'>{mean_val:.2f}</p>
                            <p style='margin:0; font-size:11px; opacity:0.9;'>Mean ± {std_val:.2f}</p>
                            <hr style='margin:10px 0; border:none; border-top:1px solid rgba(255,255,255,0.3);'>
                            <p style='margin:0; font-size:11px;'>Range: {min_val:.2f} - {max_val:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📋 Depth-Stratified Statistics")
            
            # expandable blocks per measurement, easier to scan
            for feature in selected_features:
                with st.expander(f"**{feature}** - Detailed Statistics by Depth", expanded=(feature == selected_features[0])):
                    # prep columns for the table, keep it neat
                    feature_stats = pd.DataFrame({
                        "Depth Range": stats.index,
                        "Mean": stats[(feature, "mean")].round(2),
                        "Std Dev": stats[(feature, "std")].round(2),
                        "Min": stats[(feature, "min")].round(2),
                        "Median": stats[(feature, "median")].round(2),
                        "Max": stats[(feature, "max")].round(2),
                        "Count": stats[(feature, "count")].astype(int)
                    }).reset_index(drop=True)
                    
                    # table on left, tiny profile on right
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        # styled table (blue tones only so its readable)
                        st.dataframe(
                            feature_stats.style
                            .background_gradient(cmap="Blues", subset=["Mean"], low=0.1, high=0.8)
                            .background_gradient(cmap="Blues", subset=["Std Dev"], low=0.1, high=0.6)
                            .format(precision=2, na_rep="-")
                            .set_properties(**{
                                'text-align': 'center',
                                'font-size': '10pt',
                                'border': '1px solid #ddd',
                                'color': '#000000'
                            })
                            .set_table_styles([
                                {'selector': 'th', 
                                 'props': [('background-color', '#4dabf7'), 
                                          ('color', 'white'), 
                                          ('font-weight', 'bold'),
                                          ('text-align', 'center'),
                                          ('padding', '10px'),
                                          ('font-size', '11pt')]},
                                {'selector': 'td', 
                                 'props': [('padding', '8px 12px'),
                                          ('color', '#000000')]},
                                {'selector': 'tr:hover', 
                                 'props': [('background-color', '#e3f2fd')]},
                            ]),
                            use_container_width=True,
                            height=350
                        )
                    
                    with col2:
                        # quick stats (handy)
                        st.markdown("**Quick Statistics:**")
                        st.markdown(f"""
                        - **Total Measurements:** {int(stats[(feature, 'count')].sum())}
                        - **Overall Mean:** {data[feature].mean():.2f}
                        - **Overall Std:** {data[feature].std():.2f}
                        - **Overall Range:** {data[feature].min():.2f} - {data[feature].max():.2f}
                        - **Coefficient of Variation:** {(data[feature].std() / data[feature].mean() * 100):.1f}%
                        """)
                        
                        # mini depth profile (just a quick look)
                        fig_mini = px.line(
                            feature_stats, 
                            x="Mean", 
                            y="Depth Range",
                            title=f"{feature} Profile",
                            markers=True
                        )
                        fig_mini.update_layout(
                            height=250,
                            margin=dict(l=20, r=20, t=40, b=20),
                            yaxis={'autorange': 'reversed'},
                            showlegend=False
                        )
                        st.plotly_chart(fig_mini, use_container_width=True)
            
            # === TEMPORAL STATISTICS (if data has months) ===
            if has_temporal:
                with stats_tab2:
                    st.markdown("### 🗓️ Temporal Statistics (by Month-Year)")
                    
                    # Group by month_year
                    temporal_stats = data.groupby("month_year")[selected_features].agg(
                        ["mean", "std", "min", "median", "max", "count"])
                    
                    # expandable blocks per measurement
                    for feature in selected_features:
                        with st.expander(f"**{feature}** - Temporal Variation", expanded=(feature == selected_features[0])):
                            
                            # prep data with month-year formatting
                            feature_temporal_stats = pd.DataFrame({
                                "Period": [pd.to_datetime(my + '-01').strftime('%b %Y') for my in temporal_stats.index],
                                "Mean": temporal_stats[(feature, "mean")].round(2),
                                "Std Dev": temporal_stats[(feature, "std")].round(2),
                                "Min": temporal_stats[(feature, "min")].round(2),
                                "Median": temporal_stats[(feature, "median")].round(2),
                                "Max": temporal_stats[(feature, "max")].round(2),
                                "Count": temporal_stats[(feature, "count")].astype(int)
                            }).reset_index(drop=True)
                            
                            col1, col2 = st.columns([3, 2])
                            
                            with col1:
                                st.dataframe(
                                    feature_temporal_stats.style
                                    .background_gradient(cmap="Blues", subset=["Mean"], low=0.1, high=0.8)
                                    .background_gradient(cmap="Blues", subset=["Std Dev"], low=0.1, high=0.6)
                                    .format(precision=2, na_rep="-")
                                    .set_properties(**{
                                        'text-align': 'center',
                                        'font-size': '10pt',
                                        'border': '1px solid #ddd',
                                        'color': '#000000'
                                    })
                                    .set_table_styles([
                                        {'selector': 'th', 
                                         'props': [('background-color', '#4dabf7'), 
                                                  ('color', 'white'), 
                                                  ('font-weight', 'bold'),
                                                  ('text-align', 'center'),
                                                  ('padding', '10px'),
                                                  ('font-size', '11pt')]},
                                        {'selector': 'td', 
                                         'props': [('padding', '8px 12px'),
                                                  ('color', '#000000')]},
                                        {'selector': 'tr:hover', 
                                         'props': [('background-color', '#e3f2fd')]},
                                    ]),
                                    use_container_width=True,
                                    height=250
                                )
                            
                            with col2:
                                # temporal trend plot
                                fig_temporal = px.line(
                                    feature_temporal_stats, 
                                    x="Period", 
                                    y="Mean",
                                    title=f"{feature} Temporal Trend",
                                    markers=True
                                )
                                fig_temporal.update_layout(
                                    height=250,
                                    margin=dict(l=20, r=20, t=40, b=20),
                                    showlegend=False,
                                    xaxis={'tickangle': -45}
                                )
                                st.plotly_chart(fig_temporal, use_container_width=True)
                
                # === DEPTH × PERIOD HEATMAP ===
                with stats_tab3:
                    st.markdown("### 🔀 Depth × Time Period Interaction")
                    
                    selected_heatmap_feature = st.selectbox(
                        "Select measurement for heatmap:",
                        selected_features,
                        index=selected_features.index('temperature') if 'temperature' in selected_features else 0
                    )
                    
                    # Create pivot table for heatmap
                    heatmap_data = data.groupby(['depth_bin', 'month_year'])[selected_heatmap_feature].mean().unstack(fill_value=np.nan)
                    
                    # Format column labels as "Mon YYYY"
                    period_labels = [pd.to_datetime(my + '-01').strftime('%b %Y') for my in heatmap_data.columns]
                    
                    fig_heatmap = px.imshow(
                        heatmap_data.values,
                        x=period_labels,
                        y=heatmap_data.index,
                        color_continuous_scale='RdYlBu_r',
                        labels={'x': 'Period', 'y': 'Depth Range', 'color': selected_heatmap_feature},
                        title=f"{selected_heatmap_feature} - Depth × Time Period Heatmap",
                        aspect='auto'
                    )
                    fig_heatmap.update_layout(
                        yaxis={'autorange': 'reversed'},
                        xaxis={'tickangle': -45},
                        height=500
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    st.info("💡 This heatmap shows how the measurement varies across depth and time. Darker blues = lower values, darker reds = higher values.")
            
            # downloads
            st.markdown("---")
            col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
            with col_dl1:
                st.download_button(
                    "📥 Download Full Statistics",
                    data=stats.to_csv().encode("utf-8"),
                    file_name="depth_statistics.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_dl2:
                summary_df = pd.DataFrame({
                    "Measurement": selected_features,
                    "Mean": [data[f].mean() for f in selected_features],
                    "Std": [data[f].std() for f in selected_features],
                    "Min": [data[f].min() for f in selected_features],
                    "Max": [data[f].max() for f in selected_features]
                })
                st.download_button(
                    "📥 Download Summary",
                    data=summary_df.to_csv(index=False).encode("utf-8"),
                    file_name="summary_statistics.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("👈 Select at least one measurement from the sidebar to view statistics.")

    # raw data explorer
    with tab3:
        st.markdown("### 📄 Raw Data Explorer")
        
        # quick info up top
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Total Records", len(data))
        with col_info2:
            st.metric("Depth Range", f"{data['depth'].min():.1f} - {data['depth'].max():.1f} m")
        with col_info3:
            st.metric("Measurements", len([c for c in data.columns if c in ["pH", "temperature", "turbidity", "dissolved_oxygen", "TDS"]]))
        
        st.markdown("---")
        
        # pick what columns you wanna see
        cols_display = ["latitude", "longitude", "x", "y", "depth", "pH", "temperature",
                       "turbidity", "dissolved_oxygen", "TDS", "num_sats"]
        available_cols = [c for c in cols_display if c in data.columns]
        
        selected_cols = st.multiselect(
            "Select columns to display:",
            options=available_cols,
            default=available_cols[:8] if len(available_cols) > 8 else available_cols
        )
        
        if selected_cols:
            # styled data table (blue header, zebra stripes)
            st.dataframe(
                data[selected_cols].style
                .format(precision=2, na_rep="-")
                .set_properties(**{
                    'text-align': 'center',
                    'font-size': '10pt',
                    'border': '1px solid #e0e0e0'
                })
                .set_table_styles([
                    {'selector': 'th', 
                     'props': [('background-color', '#4dabf7'), 
                              ('color', 'white'), 
                              ('font-weight', 'bold'),
                              ('text-align', 'center'),
                              ('padding', '12px'),
                              ('font-size', '11pt')]},
                    {'selector': 'td', 
                     'props': [('padding', '10px')]},
                    {'selector': 'tr:nth-child(even)', 
                     'props': [('background-color', '#f8f9fa')]},
                    {'selector': 'tr:hover', 
                     'props': [('background-color', '#e3f2fd')]},
                ]),
                use_container_width=True,
                height=500
            )
            
            # download buttons
            st.markdown("---")
            col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
            with col_dl1:
                st.download_button(
                    "📥 Download All Data",
                    data=data.to_csv(index=False).encode("utf-8"),
                    file_name="lake_data_complete.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_dl2:
                st.download_button(
                    "📥 Download Selected Columns",
                    data=data[selected_cols].to_csv(index=False).encode("utf-8"),
                    file_name="lake_data_selected.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("👈 Select at least one column to display the data.")



# predict page (train & analyze)
elif selected == "Predict":
    # Guard: avoid KeyError when no data uploaded
    if "data" not in st.session_state or st.session_state["data"] is None:
        st.info("Please upload a dataset first on the Upload page.")
        st.stop()

    data = st.session_state["data"]
    st.write("✅ Data is loaded and ready for GP preparation.")

    # -----------------------------------
    # Define input and output columns
    # -----------------------------------
    # check if we have temporal data
    has_month = st.session_state.get("has_month", False)
    
    if has_month:
        input_cols = ['x', 'y', 'depth', 'month', 'year']  # spatial + depth + time
        # Encode year as years since 2020 for better scaling
        data['year_encoded'] = data['year'] - 2020
        input_cols = ['x', 'y', 'depth', 'month', 'year_encoded']
        st.info("🕐 Training with temporal features (month and year included)")
    else:
        input_cols = ['x', 'y', 'depth']  # spatial + depth only
        st.info("📍 Training with spatial features only (no temporal data)")
    
    output_cols = [c for c in ['pH', 'temperature', 'turbidity', 'dissolved_oxygen', 'TDS'] if c in data.columns]  # Outputs present

    if not output_cols:
        st.error("No measurement columns available for prediction (pH/temperature/turbidity/dissolved_oxygen/TDS).")
        st.stop()

    # -----------------------------------
    # Normalize input and output separately
    # -----------------------------------
    scaler_x = skp.StandardScaler()
    scaler_y = skp.StandardScaler()

    X = scaler_x.fit_transform(data[input_cols])
    Y = scaler_y.fit_transform(data[output_cols])


    # Train & predict controls
    st.markdown("### Train GP and Predict")
    
    # Advanced settings in sidebar
    with st.sidebar:
        st.header("⚙️ Advanced Settings")
        with st.expander("Model Configuration", expanded=False):
            early_stopping_patience = st.number_input(
                "Early Stopping Patience",
                min_value=1,
                max_value=50,
                value=10,
                step=1,
                help="Number of iterations with no improvement before stopping training"
            )
            
            validation_split = st.slider(
                "Validation Split Ratio",
                min_value=0.1,
                max_value=0.5,
                value=0.2,
                step=0.05,
                help="Fraction of data to use for validation (0.2 = 80/20 split)"
            )
            
            rank_param = st.number_input(
                "Multitask Kernel Rank",
                min_value=1,
                max_value=5,
                value=1,
                step=1,
                help="Higher rank captures more complex task correlations"
            )

    if st.button("Train GP & Predict on Grid"):
        # Use full dataset for training (no subsampling)
        X_train_np = X
        Y_train_np = Y

        # Inform user training on full dataset may be slow, but proceed
        if len(X_train_np) > 2000:
            st.info(
                "Training on the full dataset may be slow. Please be patient..."
            )

        X_train = torch.tensor(X_train_np, dtype=torch.float32)
        Y_train = torch.tensor(Y_train_np, dtype=torch.float32)

        num_tasks = Y_train.shape[1]

        # Stratified split based on depth bins (configurable split)
        # Create depth bins for stratification
        depth_values = X_train_np[:, 2]  # depth is 3rd column
        num_bins = 10
        depth_bins = np.digitize(depth_values, bins=np.linspace(depth_values.min(), depth_values.max(), num_bins))
        
        # Manually stratify by depth bins
        np.random.seed(42)
        train_indices_list = []
        val_indices_list = []
        
        train_ratio = 1 - validation_split
        
        for bin_idx in np.unique(depth_bins):
            bin_mask = depth_bins == bin_idx
            bin_indices = np.where(bin_mask)[0]
            np.random.shuffle(bin_indices)
            
            split_point = int(train_ratio * len(bin_indices))
            train_indices_list.extend(bin_indices[:split_point])
            val_indices_list.extend(bin_indices[split_point:])
        
        train_indices = torch.tensor(train_indices_list, dtype=torch.long)
        val_indices = torch.tensor(val_indices_list, dtype=torch.long)
        
        X_train_split = X_train[train_indices]
        X_val_split = X_train[val_indices]
        Y_train_split = Y_train[train_indices]
        Y_val_split = Y_train[val_indices]

        # Define model and  likelihood (Multitask) — RBF kernel
        likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=num_tasks)
        class MultitaskExactGP(gpytorch.models.ExactGP):
            def __init__(self, train_x, train_y, likelihood, num_tasks, rank):
                super().__init__(train_x, train_y, likelihood)
                self.mean_module = gpytorch.means.MultitaskMean(gpytorch.means.ConstantMean(), num_tasks=num_tasks)
                # RBF kernel with ARD
                base_kernel = gpytorch.kernels.ScaleKernel(
                    gpytorch.kernels.RBFKernel(ard_num_dims=train_x.shape[1])
                )
                self.covar_module = gpytorch.kernels.MultitaskKernel(base_kernel, num_tasks=num_tasks, rank=rank)

            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultitaskMultivariateNormal(mean_x, covar_x)

        model = MultitaskExactGP(X_train_split, Y_train_split, likelihood, num_tasks=num_tasks, rank=rank_param)

        model.train()
        likelihood.train()

        optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
        mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

        iters = 500
        progress = st.progress(0)
        last_loss = None
        best_rmse = float("inf")
        no_improve = 0
        patience = early_stopping_patience # Early stopping patience from user settings

        # Track RMSE per task over iterations
        rmse_history = {col: [] for col in output_cols}
        rmse_history1 = {col: [] for col in output_cols}
        iteration_nums = []

        # get per-task std (original data) from scaler_y
        task_std = np.maximum(np.array(scaler_y.scale_), 1e-12)

        for i in range(iters):
            model.train()
            optimizer.zero_grad()
            output = model(X_train_split)
            loss = -mll(output, Y_train_split)
            loss.backward()
            optimizer.step()

            # Evaluate on validation set
            model.eval()
            likelihood.eval()
            with torch.no_grad(), gpytorch.settings.fast_pred_var():
                pred_dist1 = likelihood(model(X_train_split))
                pred_mean1 = pred_dist1.mean.detach().cpu().numpy()
                pred_dist = likelihood(model(X_val_split))
                pred_mean = pred_dist.mean.detach().cpu().numpy()
            y_train = Y_train_split.detach().cpu().numpy()
            y_val = Y_val_split.detach().cpu().numpy()

            # RMSE per task (currently in scaled units)
            rmse_per_task_scaled = np.sqrt(np.mean((pred_mean - y_val) ** 2, axis=0))
            rmse_per_task_scaled1 = np.sqrt(np.mean((pred_mean1 - y_train) ** 2, axis=0))
            # Convert to original units by multiplying by each task's std
            rmse_per_task = rmse_per_task_scaled * task_std
            rmse_per_task1 = rmse_per_task_scaled1 * task_std
            # Store RMSE history for each task (original units)
            for j, col in enumerate(output_cols):
                rmse_history[col].append(rmse_per_task[j])
                rmse_history1[col].append(rmse_per_task1[j])
            iteration_nums.append(i + 1)

            val_rmse = float(np.sqrt(np.mean((pred_mean - y_val) ** 2))) * float(np.mean(task_std))  # overall approx in original units
            # Early stopping
            if val_rmse < best_rmse:
                best_rmse = val_rmse
                no_improve = 0
            else:
                no_improve += 1

            if no_improve >= patience:
                st.info(f"Early stopping at iteration {i+1}")
                break

            if i % max(1, iters // 100) == 0:
                progress.progress(int((i + 1) / iters * 100))

            last_loss = loss.item()
        progress.progress(100)

        # Save optimized hyperparameters
        optimized_state_dict = model.state_dict()
        
        
        # Create model with full dataset (no optimization, just conditioning)
        model_full = MultitaskExactGP(X_train, Y_train, likelihood, num_tasks=num_tasks, rank=rank_param)
        
        # Load the optimized hyperparameters (this freezes them)
        model_full.load_state_dict(optimized_state_dict)
        
        # Set to eval mode - GP is now conditioned on full data with optimized hyperparameters
        model_full.eval()
        likelihood.eval()
        
        
        # Store the final model in session state
        st.session_state["trained_model"] = model_full
        st.session_state["likelihood"] = likelihood
        st.session_state["scaler_x"] = scaler_x
        st.session_state["scaler_y"] = scaler_y

        # -----------------------------------
        # Generate prediction grid
        # -----------------------------------
        
        # Month selection for temporal predictions
        if has_month:
            st.markdown("#### 🗓️ Temporal Prediction Settings")
            col_month1, col_month2, col_month3 = st.columns(3)
            with col_month1:
                predict_year = st.number_input(
                    "Select year:",
                    min_value=2020,
                    max_value=2030,
                    value=int(data['year'].mode()[0]) if 'year' in data.columns else 2024,
                    step=1
                )
            with col_month2:
                predict_month = st.selectbox(
                    "Select month (1-12):",
                    options=list(range(1, 13)),
                    index=5,  # default to June
                    format_func=lambda x: f"{x} - {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][x-1]}"
                )
            with col_month3:
                period_label = pd.to_datetime(f"{predict_year}-{predict_month:02d}-01").strftime('%B %Y')
                st.metric("Selected Period", period_label)
        
        # Get bounds from original data
        x_min, x_max = data['x'].min(), data['x'].max()
        y_min, y_max = data['y'].min(), data['y'].max()
        
        # Create dense 2D grid for continuous appearance
        n_grid_x = 60
        n_grid_y = 60
        
        x_grid = np.linspace(x_min, x_max, n_grid_x)
        y_grid = np.linspace(y_min, y_max, n_grid_y)
        
        # Filter XY points to stay within lake boundaries using alpha shape (more accurate than convex hull)
        from scipy.spatial import Delaunay
        
        train_points_2d = data[['x', 'y']].values
        
        # Use alpha shape approximation via Delaunay triangulation
        tri = Delaunay(train_points_2d)
        
        # Create meshgrid for XY
        X_mesh_2d, Y_mesh_2d = np.meshgrid(x_grid, y_grid, indexing='ij')
        xy_points = np.column_stack([X_mesh_2d.ravel(), Y_mesh_2d.ravel()])
        
        # Find points inside the triangulation (more accurate boundary)
        inside_mask = tri.find_simplex(xy_points) >= 0
        xy_inside = xy_points[inside_mask]
        
        # For each XY location, find max depth from training data using nearest neighbors
        from scipy.spatial import KDTree
        
        # Build KDTree for efficient nearest neighbor search
        tree = KDTree(train_points_2d)
        
        # Find k nearest neighbors for each grid point
        k_neighbors = 5
        distances, indices = tree.query(xy_inside, k=min(k_neighbors, len(train_points_2d)))
        
        # Compute max depth as weighted average of k nearest neighbors
        max_depth_at_xy = np.zeros(len(xy_inside))
        for i in range(len(xy_inside)):
            if distances.ndim == 1:  # Single neighbor case
                weights = np.array([1.0])
                neighbor_depths = data['depth'].values[indices]
            else:
                # Inverse distance weighting
                weights = 1.0 / (distances[i] + 1e-10)
                weights /= weights.sum()
                neighbor_depths = data['depth'].values[indices[i]]
            
            # Use maximum depth from neighbors (conservative approach)
            max_depth_at_xy[i] = np.max(neighbor_depths)
        
        # Generate depth points for each XY location
        n_depth_per_location = 25
        X_test_list = []
        
        for i, (x_pt, y_pt) in enumerate(xy_inside):
            max_depth = max_depth_at_xy[i]
            # Generate depths from 0 to max_depth for this location
            depths = np.linspace(0, max_depth * 0.95, n_depth_per_location)  # 95% to stay conservative
            for d in depths:
                if has_month:
                    year_encoded = predict_year - 2020
                    X_test_list.append([x_pt, y_pt, d, predict_month, year_encoded])
                else:
                    X_test_list.append([x_pt, y_pt, d])
        
        X_test_filtered = np.array(X_test_list)
        
        # Debug information
        st.info(f"Total predictions: {len(X_test_filtered)}")
        
        # Normalize test points
        X_test_scaled = scaler_x.transform(X_test_filtered)
        
        # Normalize test points
        X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
        
        # Make predictions
        model_full.eval()
        likelihood.eval()
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            pred_dist = likelihood(model_full(X_test_tensor))
            pred_mean = pred_dist.mean.detach().cpu().numpy()
            pred_var = pred_dist.variance.detach().cpu().numpy()
        
        # Convert back to original scale
        pred_mean_original = scaler_y.inverse_transform(pred_mean)
        task_std = np.array(scaler_y.scale_)
        pred_std_original = np.sqrt(pred_var) * task_std[np.newaxis, :]
        
        # Create prediction dataframe
        if has_month:
            pred_df = pd.DataFrame(X_test_filtered, columns=['x', 'y', 'depth', 'month', 'year_encoded'])
            # Convert year_encoded back to actual year
            pred_df['year'] = pred_df['year_encoded'] + 2020
            pred_df = pred_df.drop(columns=['year_encoded'])
        else:
            pred_df = pd.DataFrame(X_test_filtered, columns=['x', 'y', 'depth'])
        
        for j, col in enumerate(output_cols):
            pred_df[f'{col}_pred'] = pred_mean_original[:, j]
            pred_df[f'{col}_std'] = pred_std_original[:, j]
        
        if has_month:
            period_label = pd.to_datetime(f"{predict_year}-{predict_month:02d}-01").strftime('%B %Y')
            st.success(f"Predictions complete! Generated {len(pred_df)} predictions for {period_label}.")
        else:
            st.success(f"Predictions complete! Generated {len(pred_df)} predictions.")
        
        # Store predictions
        st.session_state["predictions"] = pred_df
        st.session_state["output_cols"] = output_cols
        if has_month:
            st.session_state["predict_month"] = predict_month
            st.session_state["predict_year"] = predict_year

    # -----------------------------------
    # Tabbed Visualization (outside button block)
    # -----------------------------------
    if "predictions" in st.session_state and st.session_state["predictions"] is not None:
        pred_df = st.session_state["predictions"]
        output_cols = st.session_state["output_cols"]
        predict_month = st.session_state.get("predict_month", None)
        predict_year = st.session_state.get("predict_year", None)
        
        # Download button with period in filename if applicable
        if predict_month and predict_year:
            filename = f"gp_predictions_{predict_year}_{predict_month:02d}.csv"
        else:
            filename = "gp_predictions.csv"
            
        st.download_button(
            "Download Predictions CSV",
            data=pred_df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv",
        )
        
        st.markdown("### Prediction Results")
        
        # Add period selector for analyzing different future periods
        if has_month and "trained_model" in st.session_state:
            st.markdown("#### 🔮 Analyze Predictions for Different Time Periods")
            
            col_year_sel, col_month_sel, col_button = st.columns([2, 2, 1])
            
            with col_year_sel:
                analyze_year = st.number_input(
                    "Year:",
                    min_value=2020,
                    max_value=2030,
                    value=predict_year if predict_year else 2024,
                    step=1,
                    key="analyze_year_input"
                )
            
            with col_month_sel:
                analyze_month = st.selectbox(
                    "Select month to analyze:",
                    options=list(range(1, 13)),
                    index=predict_month - 1 if predict_month else 5,
                    format_func=lambda x: f"{x} - {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][x-1]}",
                    key="analyze_month_selector"
                )
            
            with col_button:
                st.write("")  # spacer
                st.write("")  # spacer
                period_label = pd.to_datetime(f"{analyze_year}-{analyze_month:02d}-01").strftime('%B %Y')
                if st.button(f"🔄 Generate for {period_label}", key="regenerate_period"):
                    # Re-generate predictions for the selected period
                    with st.spinner(f"Generating predictions for {period_label}..."):
                        # Retrieve stored model and scalers
                        model_full = st.session_state["trained_model"]
                        likelihood = st.session_state["likelihood"]
                        scaler_x = st.session_state["scaler_x"]
                        scaler_y = st.session_state["scaler_y"]
                        
                        # Re-use the same grid generation logic but with new month and year
                        x_min, x_max = data['x'].min(), data['x'].max()
                        y_min, y_max = data['y'].min(), data['y'].max()
                        
                        n_grid_x = 60
                        n_grid_y = 60
                        
                        x_grid = np.linspace(x_min, x_max, n_grid_x)
                        y_grid = np.linspace(y_min, y_max, n_grid_y)
                        
                        from scipy.spatial import Delaunay, KDTree
                        
                        train_points_2d = data[['x', 'y']].values
                        tri = Delaunay(train_points_2d)
                        
                        X_mesh_2d, Y_mesh_2d = np.meshgrid(x_grid, y_grid, indexing='ij')
                        xy_points = np.column_stack([X_mesh_2d.ravel(), Y_mesh_2d.ravel()])
                        inside_mask = tri.find_simplex(xy_points) >= 0
                        xy_inside = xy_points[inside_mask]
                        
                        tree = KDTree(train_points_2d)
                        k_neighbors = 5
                        distances, indices = tree.query(xy_inside, k=min(k_neighbors, len(train_points_2d)))
                        
                        max_depth_at_xy = np.zeros(len(xy_inside))
                        for i in range(len(xy_inside)):
                            if distances.ndim == 1:
                                weights = np.array([1.0])
                                neighbor_depths = data['depth'].values[indices]
                            else:
                                weights = 1.0 / (distances[i] + 1e-10)
                                weights /= weights.sum()
                                neighbor_depths = data['depth'].values[indices[i]]
                            max_depth_at_xy[i] = np.max(neighbor_depths)
                        
                        n_depth_per_location = 25
                        X_test_list = []
                        
                        for i, (x_pt, y_pt) in enumerate(xy_inside):
                            max_depth = max_depth_at_xy[i]
                            depths = np.linspace(0, max_depth * 0.95, n_depth_per_location)
                            for d in depths:
                                year_encoded = analyze_year - 2020
                                X_test_list.append([x_pt, y_pt, d, analyze_month, year_encoded])
                        
                        X_test_filtered = np.array(X_test_list)
                        X_test_scaled = scaler_x.transform(X_test_filtered)
                        X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
                        
                        model_full.eval()
                        likelihood.eval()
                        with torch.no_grad(), gpytorch.settings.fast_pred_var():
                            pred_dist = likelihood(model_full(X_test_tensor))
                            pred_mean = pred_dist.mean.detach().cpu().numpy()
                            pred_var = pred_dist.variance.detach().cpu().numpy()
                        
                        pred_mean_original = scaler_y.inverse_transform(pred_mean)
                        task_std = np.array(scaler_y.scale_)
                        pred_std_original = np.sqrt(pred_var) * task_std[np.newaxis, :]
                        
                        pred_df = pd.DataFrame(X_test_filtered, columns=['x', 'y', 'depth', 'month', 'year_encoded'])
                        # Convert year_encoded back to actual year
                        pred_df['year'] = pred_df['year_encoded'] + 2020
                        pred_df = pred_df.drop(columns=['year_encoded'])
                        
                        for j, col in enumerate(output_cols):
                            pred_df[f'{col}_pred'] = pred_mean_original[:, j]
                            pred_df[f'{col}_std'] = pred_std_original[:, j]
                        
                        st.session_state["predictions"] = pred_df
                        st.session_state["predict_month"] = analyze_month
                        st.session_state["predict_year"] = analyze_year
                        
                        period_label_success = pd.to_datetime(f"{analyze_year}-{analyze_month:02d}-01").strftime('%B %Y')
                        st.success(f"✅ Predictions regenerated for {period_label_success}!")
                        st.rerun()
            
            st.markdown("---")
        
        # Show temporal context if available
        if predict_month and predict_year:
            period_label = pd.to_datetime(f"{predict_year}-{predict_month:02d}-01").strftime('%B %Y')
            st.info(f"🗓️ Predictions shown for **{period_label}**")
        
        # Check if we have temporal training data
        has_temporal_training = has_month and 'month_year' in data.columns and data['month_year'].nunique() > 1
        
        if has_temporal_training:
            tab1, tab2, tab3, tab4 = st.tabs(["3D Thermal Visualization", "Measurement vs Depth", "Temporal Trends", "Advanced Analysis"])
        else:
            tab1, tab2, tab3 = st.tabs(["3D Thermal Visualization", "Measurement vs Depth", "Advanced Analysis"])
        
        # ----- TAB 1: 3D Thermal Plot -----
        with tab1:
            # User selection for which measurement to visualize
            selected_measurement = st.selectbox(
                "Select measurement to visualize:",
                output_cols,
                index=output_cols.index('temperature') if 'temperature' in output_cols else 0
            )
            
            # Display uncertainty metrics
            st.markdown("#### Model Performance Metrics")
            cols_metrics = st.columns(len(output_cols))
            for idx, col in enumerate(output_cols):
                with cols_metrics[idx]:
                    avg_std = pred_df[f'{col}_std'].mean()
                    st.metric(
                        label=f"{col}",
                        value=f"±{avg_std:.2f}",
                        delta=f"Avg Uncertainty",
                        delta_color="off"
                    )
            
            # Combine training data and predictions
            train_df = data[['x', 'y', 'depth']].copy()
            for col in output_cols:
                train_df[f'{col}_pred'] = data[col].values
            train_df['source'] = 'Training Data'
            
            pred_df_display = pred_df.copy()
            pred_df_display['source'] = 'Prediction'
            
            # Combine both datasets
            combined_df = pd.concat([
                train_df[['x', 'y', 'depth', f'{selected_measurement}_pred', 'source']],
                pred_df_display[['x', 'y', 'depth', f'{selected_measurement}_pred', 'source']]
            ], ignore_index=True)
            
            # Invert depth for visualization
            combined_df['depth_inverted'] = -combined_df['depth']
            
            # Create 3D scatter plot with smaller markers for continuous appearance
            fig_3d = px.scatter_3d(
                combined_df,
                x='x',
                y='y',
                z='depth_inverted',
                color=f'{selected_measurement}_pred',
                symbol='source',
                title=f'3D Thermal Plot: {selected_measurement}',
                labels={
                    'x': 'X (m)',
                    'y': 'Y (m)',
                    'depth_inverted': 'Depth (m)',
                    f'{selected_measurement}_pred': selected_measurement
                },
                color_continuous_scale='Thermal',
                opacity=0.8
            )
            
            # Update marker sizes - smaller for predictions, larger for training
            fig_3d.update_traces(
                marker=dict(size=2, opacity=0.9),
                selector=dict(name='Prediction')
            )
            fig_3d.update_traces(
                marker=dict(size=4, opacity=1.0),
                selector=dict(name='Training Data')
            )
            
            fig_3d.update_layout(
                scene=dict(
                    xaxis_title="X (m)",
                    yaxis_title="Y (m)",
                    zaxis_title="Depth (m)",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.2)
                    )
                ),
                height=700,
                paper_bgcolor="#f0f4f8"
            )
            
            st.plotly_chart(fig_3d, use_container_width=True)
        
        # ----- TAB 2: Measurement vs Depth -----
        with tab2:
            st.markdown("#### Measurement Profiles vs Depth")
            
            selected_measurement_tab2 = st.selectbox(
                "Select measurement:",
                output_cols,
                index=output_cols.index('temperature') if 'temperature' in output_cols else 0,
                key="tab2_measurement"
            )
            
            # Prepare data
            train_depth = data['depth'].values
            train_values = data[selected_measurement_tab2].values
            
            # Create dataframe for predictions with bounds
            pred_plot_df = pd.DataFrame({
                "Depth": pred_df['depth'].values,
                "Predicted": pred_df[f'{selected_measurement_tab2}_pred'].values,
                "Lower Bound": pred_df[f'{selected_measurement_tab2}_pred'].values - 1.96 * pred_df[f'{selected_measurement_tab2}_std'].values,
                "Upper Bound": pred_df[f'{selected_measurement_tab2}_pred'].values + 1.96 * pred_df[f'{selected_measurement_tab2}_std'].values
            })
            
            # Sort by depth for better visualization
            pred_plot_df = pred_plot_df.sort_values("Depth")
            
            # Create scatter plot with training data
            fig_depth = px.scatter(
                x=train_depth,
                y=train_values,
                labels={'x': 'Depth (m)', 'y': selected_measurement_tab2},
                title=f'{selected_measurement_tab2} vs Depth'
            )
            fig_depth.update_traces(
                marker=dict(color='blue', size=6),
                name='Training Data'
            )
            
            # Add predictions
            fig_depth.add_scatter(
                x=pred_plot_df["Depth"],
                y=pred_plot_df["Predicted"],
                mode='markers',
                marker=dict(color='red', size=4, opacity=0.6),
                name='Predictions'
            )
            
            # Add uncertainty bands
            fig_depth.add_scatter(
                x=pred_plot_df["Depth"],
                y=pred_plot_df["Upper Bound"],
                mode='lines',
                name='Upper 95% CI',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            )
            
            fig_depth.add_scatter(
                x=pred_plot_df["Depth"],
                y=pred_plot_df["Lower Bound"],
                mode='lines',
                name='95% Confidence Interval',
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.2)',
                line=dict(width=0),
                hoverinfo='skip'
            )
            
            fig_depth.update_layout(
                template="simple_white",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="Depth (m)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title=selected_measurement_tab2),
                height=600,
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_depth, use_container_width=True)
        
        # ----- TAB 3 or 4: Temporal Trends (if temporal data exists) -----
        if has_temporal_training:
            with tab3:
                st.markdown("#### 🗓️ Temporal Trends Analysis")
                
                # Get unique periods from training data
                training_periods = sorted(data['month_year'].unique())
                
                st.info(f"📊 Training data includes {len(training_periods)} time periods: {', '.join([pd.to_datetime(p + '-01').strftime('%b %Y') for p in training_periods])}")
                
                # Select measurement for temporal analysis
                temp_feature = st.selectbox(
                    "Select measurement for temporal analysis:",
                    output_cols,
                    index=output_cols.index('temperature') if 'temperature' in output_cols else 0,
                    key="temporal_feature"
                )
                
                # Select depth range to analyze
                depth_ranges = st.slider(
                    "Select depth range to analyze:",
                    min_value=float(data['depth'].min()),
                    max_value=float(data['depth'].max()),
                    value=(float(data['depth'].min()), float(data['depth'].max())),
                    step=0.5
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Training Data - Temporal Averages**")
                    # Filter training data by depth range
                    depth_mask = (data['depth'] >= depth_ranges[0]) & (data['depth'] <= depth_ranges[1])
                    temporal_avg_train = data[depth_mask].groupby('month_year')[temp_feature].agg(['mean', 'std', 'count']).reset_index()
                    
                    # Format period labels
                    temporal_avg_train['Period'] = temporal_avg_train['month_year'].apply(lambda x: pd.to_datetime(x + '-01').strftime('%b %Y'))
                    
                    # Plot training temporal trend
                    fig_train_temporal = px.line(
                        temporal_avg_train,
                        x='Period',
                        y='mean',
                        error_y='std',
                        markers=True,
                        title=f"{temp_feature} - Observed Temporal Trend",
                        labels={'mean': temp_feature, 'Period': 'Time Period'}
                    )
                    fig_train_temporal.update_layout(height=350, xaxis={'tickangle': -45})
                    st.plotly_chart(fig_train_temporal, use_container_width=True)
                    
                    # Show statistics table
                    st.dataframe(
                        temporal_avg_train[['Period', 'mean', 'std', 'count']].rename(columns={'mean': 'Mean', 'std': 'Std', 'count': 'Count'}).style
                        .format({'Mean': '{:.2f}', 'Std': '{:.2f}', 'Count': '{:.0f}'})
                        .background_gradient(cmap="Blues", subset=['Mean'], low=0.1, high=0.8),
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("**Depth Profiles by Time Period**")
                    
                    # Select periods to compare
                    compare_periods = st.multiselect(
                        "Select periods to compare:",
                        options=training_periods,
                        default=training_periods[:min(3, len(training_periods))],
                        format_func=lambda x: pd.to_datetime(x + '-01').strftime('%b %Y')
                    )
                    
                    if compare_periods:
                        # Create depth profiles for selected periods
                        fig_depth_period = px.scatter()
                        
                        for period in compare_periods:
                            period_data = data[data['month_year'] == period]
                            period_profile = period_data.groupby('depth')[temp_feature].mean().reset_index()
                            period_label = pd.to_datetime(period + '-01').strftime('%b %Y')
                            
                            fig_depth_period.add_scatter(
                                x=period_profile[temp_feature],
                                y=period_profile['depth'],
                                mode='lines+markers',
                                name=period_label,
                                line=dict(width=2),
                                marker=dict(size=6)
                            )
                        
                        fig_depth_period.update_layout(
                            title=f"{temp_feature} Depth Profiles by Time Period",
                            xaxis_title=temp_feature,
                            yaxis_title="Depth (m)",
                            yaxis=dict(autorange='reversed'),
                            height=350,
                            hovermode='closest'
                        )
                        st.plotly_chart(fig_depth_period, use_container_width=True)
                    else:
                        st.info("👈 Select periods to compare depth profiles")
                
                # Temporal pattern summary
                st.markdown("---")
                st.markdown("**📈 Temporal Pattern Summary**")
                
                temporal_summary = []
                for period in training_periods:
                    period_data = data[data['month_year'] == period]
                    period_label = pd.to_datetime(period + '-01').strftime('%b %Y')
                    temporal_summary.append({
                        'Period': period_label,
                        'Mean': period_data[temp_feature].mean(),
                        'Std': period_data[temp_feature].std(),
                        'Min': period_data[temp_feature].min(),
                        'Max': period_data[temp_feature].max(),
                        'Samples': len(period_data)
                    })
                
                summary_df = pd.DataFrame(temporal_summary)
                st.dataframe(
                    summary_df.style
                    .format({'Mean': '{:.2f}', 'Std': '{:.2f}', 'Min': '{:.2f}', 'Max': '{:.2f}', 'Samples': '{:.0f}'})
                    .background_gradient(cmap="RdYlBu_r", subset=['Mean'], vmin=summary_df['Mean'].min(), vmax=summary_df['Mean'].max()),
                    use_container_width=True
                )
        
        # ----- Advanced Analysis Tab -----
        advanced_tab = tab4 if has_temporal_training else tab3
        with advanced_tab:
            st.markdown("#### Advanced Analysis")

            # --- Thermocline detection (if temperature available) ---
            if 'temperature' in output_cols:
                st.markdown("**Thermocline Analysis**")
                temp_profile = (
                    pred_df[['depth', 'temperature_pred']]
                    .groupby('depth', as_index=False)
                    .mean()
                    .sort_values('depth')
                )
                depths_raw = temp_profile['depth'].to_numpy()
                temps_raw = temp_profile['temperature_pred'].to_numpy()

                thermocline_depth = None
                max_grad = None
                temp_at_tc = None

                if len(depths_raw) >= 4:
                    # Resample to finer evenly spaced depths for accurate gradients
                    dmin, dmax = float(depths_raw.min()), float(depths_raw.max())
                    n_samples = max(100, len(depths_raw) * 5)  # Much finer grid
                    depths = np.linspace(dmin, dmax, n_samples)
                    temps_interp = np.interp(depths, depths_raw, temps_raw)

                    # Apply stronger Savitzky-Golay smoothing for noise reduction
                    from scipy.signal import savgol_filter
                    if n_samples >= 15:
                        window = min(15, n_samples - (1 - n_samples % 2))
                        if window % 2 == 0:
                            window -= 1
                        window = max(5, window)
                        temps_smooth = savgol_filter(temps_interp, window_length=window, polyorder=3)
                    elif n_samples >= 5:
                        window = n_samples if n_samples % 2 == 1 else n_samples - 1
                        temps_smooth = savgol_filter(temps_interp, window_length=window, polyorder=2)
                    else:
                        temps_smooth = temps_interp

                    # Compute high-precision central-difference gradient on uniform grid
                    dz = depths[1] - depths[0]
                    grad = np.empty_like(temps_smooth)
                    grad[1:-1] = (temps_smooth[2:] - temps_smooth[:-2]) / (2 * dz)
                    grad[0] = (temps_smooth[1] - temps_smooth[0]) / dz
                    grad[-1] = (temps_smooth[-1] - temps_smooth[-2]) / dz

                    # Restrict analysis to interior to avoid boundary artifacts
                    interior = slice(2, len(depths) - 2)  # More conservative interior
                    depths_int = depths[interior]
                    grad_int = grad[interior]

                    if len(grad_int):
                        # Use smaller rolling window for more localized gradient detection
                        import pandas as pd
                        win = max(3, int(0.05 * len(grad_int)))  # Reduced from 0.1 to 0.05
                        win = win if win % 2 == 1 else win + 1
                        grad_roll = pd.Series(grad_int).rolling(window=win, center=True).median().to_numpy()
                        # Fallback if NaNs at edges
                        mask_valid = ~np.isnan(grad_roll)
                        if mask_valid.any():
                            idx = int(np.argmin(grad_roll[mask_valid]))
                            # Map idx in masked array back to full interior index
                            valid_indices = np.where(mask_valid)[0]
                            interior_idx = valid_indices[idx]
                            thermocline_depth = float(depths_int[interior_idx])
                            max_grad = float(grad_roll[mask_valid][idx])
                            # Get temperature at thermocline from smooth curve
                            full_idx = interior_idx + 2  # offset by interior slice start
                            temp_at_tc = float(temps_smooth[full_idx])

                col_th1, col_th2 = st.columns(2)
                with col_th1:
                    st.metric("Thermocline depth (m)", f"{thermocline_depth:.2f}" if thermocline_depth is not None else "N/A")
                with col_th2:
                    st.metric("Max temp gradient (°C/m)", f"{max_grad:.3f}" if max_grad is not None else "N/A")

                fig_tc = px.line(temp_profile, x='depth', y='temperature_pred', title='Mean Temperature vs Depth')
                fig_tc.update_xaxes(title='Depth (m)')
                fig_tc.update_yaxes(title='Temperature (°C)')

                # Add gradient minimum marker if available
                if thermocline_depth is not None:
                    fig_tc.add_vline(x=thermocline_depth, line_dash='dash', line_color='red', annotation_text='Thermocline', annotation_position='top right')
                    # Add tangent line at thermocline depth if slope and value available
                    if (max_grad is not None) and (temp_at_tc is not None):
                        # Choose a small x-span around thermocline for tangent visualization
                        x0 = thermocline_depth - 0.5 * (depths.max() - depths.min()) * 0.05
                        x1 = thermocline_depth + 0.5 * (depths.max() - depths.min()) * 0.05
                        y0 = temp_at_tc + max_grad * (x0 - thermocline_depth)
                        y1 = temp_at_tc + max_grad * (x1 - thermocline_depth)
                        fig_tc.add_scatter(x=[x0, x1], y=[y0, y1], mode='lines', name='Tangent at thermocline', line=dict(color='red', width=2, dash='dot'))

                st.plotly_chart(fig_tc, use_container_width=True)
                st.divider()

            # --- Hypoxia risk (if dissolved oxygen available) ---
            if 'dissolved_oxygen' in output_cols:
                st.markdown("**Hypoxia Risk**")
                hyp_thresh = st.slider("Hypoxia threshold (mg/L)", 1.0, 6.0, 4.0, 0.5, key="hyp_thresh")
                do_values = pred_df['dissolved_oxygen_pred']
                below_mask = do_values < hyp_thresh
                frac_below = below_mask.mean() if len(do_values) else 0.0
                min_do = do_values.min() if len(do_values) else np.nan
                # Depth of first crossing (shallowest depth where DO below threshold)
                depth_below = pred_df.loc[below_mask, 'depth'] if len(do_values) else pd.Series([], dtype=float)
                first_depth = depth_below.min() if not depth_below.empty else np.nan
                col_do1, col_do2, col_do3 = st.columns(3)
                with col_do1:
                    st.metric("Area fraction below threshold", f"{frac_below*100:.1f}%")
                with col_do2:
                    st.metric("Min DO (mg/L)", f"{min_do:.2f}" if not np.isnan(min_do) else "N/A")
                with col_do3:
                    st.metric("Shallowest hypoxic depth (m)", f"{first_depth:.2f}" if not np.isnan(first_depth) else "None")

                do_profile = (
                    pred_df[['depth', 'dissolved_oxygen_pred']]
                    .groupby('depth', as_index=False)
                    .median()
                    .sort_values('depth')
                )
                fig_do = px.line(do_profile, x='depth', y='dissolved_oxygen_pred', title='Median DO vs Depth')
                fig_do.add_hline(y=hyp_thresh, line_dash="dash", line_color="red", annotation_text="Threshold", annotation_position="right")
                fig_do.update_xaxes(title='Depth (m)')
                fig_do.update_yaxes(title='Dissolved Oxygen (mg/L)')
                st.plotly_chart(fig_do, use_container_width=True)
                st.divider()

            # --- Horizontal temperature gradient (if temperature available) ---
            if 'temperature' in output_cols:
                st.markdown("**Horizontal Temperature Gradient**")
                depth_for_gradient = st.slider("Select depth for horizontal gradient (m)", 
                    float(pred_df['depth'].min()), 
                    float(pred_df['depth'].max()), 
                    float(pred_df['depth'].min()), 
                    0.5, 
                    key="horiz_grad_depth")
                
                # Filter predictions near selected depth (±0.5m tolerance)
                depth_slice = pred_df[abs(pred_df['depth'] - depth_for_gradient) <= 0.5].copy()
                
                if len(depth_slice) > 10:
                    # Create 2D heatmap at this depth
                    fig_heatmap = px.scatter(
                        depth_slice, 
                        x='x', 
                        y='y', 
                        color='temperature_pred',
                        title=f'Temperature at {depth_for_gradient:.1f}m depth',
                        color_continuous_scale='Thermal',
                        labels={'temperature_pred': 'Temperature (°C)'}
                    )
                    fig_heatmap.update_traces(marker=dict(size=8))
                    fig_heatmap.update_layout(height=500)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    # Calculate horizontal gradient magnitude
                    if len(depth_slice) >= 3:
                        from scipy.interpolate import griddata
                        x_pts = depth_slice['x'].values
                        y_pts = depth_slice['y'].values
                        temp_vals = depth_slice['temperature_pred'].values
                        
                        # Create regular grid
                        x_grid = np.linspace(x_pts.min(), x_pts.max(), 30)
                        y_grid = np.linspace(y_pts.min(), y_pts.max(), 30)
                        X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
                        
                        # Interpolate temperature
                        T_grid = griddata((x_pts, y_pts), temp_vals, (X_grid, Y_grid), method='linear')
                        
                        # Compute gradients
                        if not np.all(np.isnan(T_grid)):
                            dT_dx, dT_dy = np.gradient(T_grid, x_grid[1]-x_grid[0], y_grid[1]-y_grid[0])
                            grad_mag = np.sqrt(dT_dx**2 + dT_dy**2)
                            max_grad_horiz = np.nanmax(grad_mag)
                            mean_grad_horiz = np.nanmean(grad_mag)
                            
                            col_hg1, col_hg2 = st.columns(2)
                            with col_hg1:
                                st.metric("Max horizontal gradient (°C/m)", f"{max_grad_horiz:.4f}")
                            with col_hg2:
                                st.metric("Mean horizontal gradient (°C/m)", f"{mean_grad_horiz:.4f}")
                else:
                    st.info(f"Not enough data points at depth {depth_for_gradient:.1f}m for gradient analysis")
                st.divider()

            # --- Uncertainty summary for any measurement ---
            st.markdown("**Uncertainty Summary**")
            sel_unc = st.selectbox("Measurement for uncertainty stats", output_cols, key="uncertainty_measurement")
            mean_pred = pred_df[f'{sel_unc}_pred']
            std_pred = pred_df[f'{sel_unc}_std']
            p10 = np.percentile(mean_pred, 10) if len(mean_pred) else np.nan
            p50 = np.percentile(mean_pred, 50) if len(mean_pred) else np.nan
            p90 = np.percentile(mean_pred, 90) if len(mean_pred) else np.nan
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)
            with col_u1:
                st.metric("Mean σ", f"{std_pred.mean():.3f}" if len(std_pred) else "N/A")
            with col_u2:
                st.metric("p10", f"{p10:.3f}" if not np.isnan(p10) else "N/A")
            with col_u3:
                st.metric("p50", f"{p50:.3f}" if not np.isnan(p50) else "N/A")
            with col_u4:
                st.metric("p90", f"{p90:.3f}" if not np.isnan(p90) else "N/A")

            # Depth-binned uncertainty
            unc_profile = (
                pred_df[['depth', f'{sel_unc}_std']]
                .groupby('depth', as_index=False)
                .mean()
                .sort_values('depth')
            )
            fig_unc = px.line(unc_profile, x='depth', y=f'{sel_unc}_std', title=f'Mean Uncertainty vs Depth for {sel_unc}')
            fig_unc.update_xaxes(title='Depth (m)')
            fig_unc.update_yaxes(title='Std Dev')
            st.plotly_chart(fig_unc, use_container_width=True)


        # # Plot individual RMSE curves for each task (original units)
        # st.markdown("### RMSE per Task Over Training Iterations (original units)")
        
        # for col in output_cols:
        #     rmse_curve_df = pd.DataFrame({
        #         "Iteration": iteration_nums,
        #         "Validation RMSE": rmse_history[col],
        #         "Training RMSE": rmse_history1[col]
        #     })
            
        #     fig_line = px.line(
        #         rmse_curve_df,
        #         x="Iteration",
        #         y=["Validation RMSE", "Training RMSE"],
        #         title=f"RMSE for {col} over iterations",
        #         markers=True
        #     )
        #     fig_line.update_layout(
        #         template="simple_white",
        #         plot_bgcolor="rgba(0,0,0,0)",
        #         paper_bgcolor="rgba(0,0,0,0)",
        #         xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        #         yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        #         hovermode="x unified"
        #     )
        #     st.plotly_chart(fig_line, use_container_width=True)

        # # Get final predictions with uncertainty for validation set
        # model.eval()
        # likelihood.eval()
        # with torch.no_grad(), gpytorch.settings.fast_pred_var():
        #     pred_dist_final = likelihood(model(X_val_split))
        #     pred_mean_final = pred_dist_final.mean.detach().cpu().numpy()
        #     pred_var_final = pred_dist_final.variance.detach().cpu().numpy()
        
        # # Convert predictions and uncertainty back to original scale
        # pred_mean_original = scaler_y.inverse_transform(pred_mean_final)
        # pred_std_original = np.sqrt(pred_var_final) * task_std[np.newaxis, :]
        
        # # Get actual validation data in original scale
        # y_val_original = scaler_y.inverse_transform(Y_val_split.detach().cpu().numpy())
        
        # # Get validation depths
        # X_val_original = scaler_x.inverse_transform(X_val_split.detach().cpu().numpy())
        # val_depths = X_val_original[:, 2]  # depth is the 3rd column
        
        # # Plot validation data vs predictions with uncertainty for each measurement
        # st.markdown("### Validation Data vs Predictions with Uncertainty")
        
        # for j, col in enumerate(output_cols):
        #     # Create dataframe for plotting
        #     plot_df = pd.DataFrame({
        #         "Depth": val_depths,
        #         "Actual": y_val_original[:, j],
        #         "Predicted": pred_mean_original[:, j],
        #         "Lower Bound": pred_mean_original[:, j] - 1.96 * pred_std_original[:, j],
        #         "Upper Bound": pred_mean_original[:, j] + 1.96 * pred_std_original[:, j]
        #     })
            
        #     # Sort by depth for better visualization
        #     plot_df = plot_df.sort_values("Depth")
            
        #     # Create scatter plot with uncertainty bands
        #     fig = px.scatter(
        #         plot_df,
        #         x="Depth",
        #         y="Actual",
        #         title=f"{col}: Actual vs Predicted (with 95% uncertainty)",
        #         labels={"Actual": col}
        #     )
            
        #     # Add predicted values
        #     fig.add_scatter(
        #         x=plot_df["Depth"],
        #         y=plot_df["Predicted"],
        #         mode="markers",
        #         name="Predicted",
        #         marker=dict(color="red", size=6)
        #     )
            
        #     # Add uncertainty band
        #     fig.add_scatter(
        #         x=plot_df["Depth"],
        #         y=plot_df["Upper Bound"],
        #         mode="lines",
        #         name="Upper 95% CI",
        #         line=dict(width=0),
        #         showlegend=False,
        #         hoverinfo="skip"
        #     )
            
        #     fig.add_scatter(
        #         x=plot_df["Depth"],
        #         y=plot_df["Lower Bound"],
        #         mode="lines",
        #         name="95% Confidence Interval",
        #         fill="tonexty",
        #         fillcolor="rgba(255,0,0,0.2)",
        #         line=dict(width=0),
        #         hoverinfo="skip"
        #     )
            
        #     fig.update_layout(
        #         template="simple_white",
        #         plot_bgcolor="rgba(0,0,0,0)",
        #         paper_bgcolor="rgba(0,0,0,0)",
        #         xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="Depth (m)"),
        #         yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title=col),
        #         hovermode="x unified"
        #     )
            
        #     st.plotly_chart(fig, use_container_width=True)


elif selected == "Help":
    st.header("📖 User Guide")
    st.markdown("---")
    
    # Introduction
    st.markdown("""
    ### Welcome to the Lake Water Quality Dashboard
    
    This application helps you analyze and predict lake water quality measurements using advanced 
    Gaussian Process machine learning models. Follow the steps below to get started.
    """)
    
    # Step-by-step guide
    st.markdown("### 🚀 Getting Started")
    
    with st.expander("**Step 1: Prepare Your Data**", expanded=True):
        st.markdown("""
        Your CSV file must include the following columns:
        - `latitude` - GPS latitude coordinates
        - `longitude` - GPS longitude coordinates  
        - `depth` - Water depth in meters
        - `num_sats` (optional) - Number of GPS satellites (for quality filtering)
        
        **Water Quality Measurements** (at least one required):
        - `pH` - pH level
        - `temperature` - Water temperature in °C
        - `turbidity` - Turbidity in NTU
        - `dissolved_oxygen` - Dissolved oxygen in mg/L
        - `TDS` - Total dissolved solids in mg/L
        
        **Example CSV structure:**
        ```
        latitude,longitude,depth,pH,temperature,turbidity,dissolved_oxygen,TDS,num_sats
        59.3293,18.0686,1.5,7.2,18.5,2.3,8.5,120,6
        59.3294,18.0687,2.0,7.1,17.8,2.5,8.2,118,5
        ```
        """)
    
    with st.expander("**Step 2: Upload Your Data**"):
        st.markdown("""
        1. Navigate to the **Upload** page using the sidebar menu
        2. Click the file upload button and select your CSV file
        3. The system will automatically:
           - Filter out unreliable GPS points (num_sats < 4)
           - Convert GPS coordinates to Cartesian (x, y) coordinates
           - Display your data in 3D visualization
        
        **Controls:**
        - Select which measurements to display in the statistics table
        - Adjust depth bin width for grouping data
        - Choose color scheme for 3D visualization
        """)
    
    with st.expander("**Step 3: Train the Prediction Model**"):
        st.markdown("""
        1. Go to the **Predict** page using the sidebar
        2. (Optional) Adjust **Advanced Settings** in the sidebar:
           - **Early Stopping Patience** (default: 10) - How long to wait for improvement
           - **Validation Split Ratio** (default: 0.2) - Fraction of data for validation
           - **Multitask Kernel Rank** (default: 1) - Model complexity (higher = more complex correlations)
        
        3. Click **"Train GP & Predict on Grid"**
        4. The model will:
           - Split data into training/validation sets (stratified by depth)
           - Optimize hyperparameters using the training set
           - Retrain on the full dataset with optimized settings
           - Generate predictions on a dense 3D grid throughout the lake
        
        **Note:** Training may take 1-5 minutes depending on data size.
        """)
    
    with st.expander("**Step 4: Analyze Results**"):
        st.markdown("""
        After training, explore three result tabs:
        
        **Tab 1: 3D Thermal Visualization**
        - Interactive 3D plot showing spatial distribution of measurements
        - Blue points = training data, Red points = predictions
        - Select different measurements from the dropdown
        - Model uncertainty metrics displayed as cards
        
        **Tab 2: Measurement vs Depth**
        - Depth profile plots for each measurement
        - Blue dots = training observations
        - Red dots = model predictions
        - Shaded area = 95% confidence interval
        
        **Tab 3: Advanced Analysis**
        - **Thermocline Detection**: Identifies temperature stratification layer
        - **Hypoxia Risk**: Analyzes dissolved oxygen depletion zones
        - **Horizontal Gradients**: 2D temperature variation at specific depths
        - **Uncertainty Summary**: Statistical distribution of prediction confidence
        """)
    
    with st.expander("**Step 5: Export Results**"):
        st.markdown("""
        - Download prediction CSV with all predicted values and uncertainties
        - Download statistics tables for further analysis
        - Download layer statistics (if applicable)
        """)
    
    st.markdown("---")
    st.markdown("### 📊 Understanding the Outputs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Model Metrics:**
        - **RMSE** - Root Mean Square Error (lower is better)
        - **σ (sigma)** - Standard deviation (uncertainty)
        - **95% CI** - 95% confidence interval
        - **p10/p50/p90** - 10th, 50th, 90th percentiles
        """)
    
    with col2:
        st.markdown("""
        **Lake Stratification:**
        - **Thermocline** - Layer of rapid temperature change
        - **Epilimnion** - Warm surface layer
        - **Metalimnion** - Transition zone (thermocline)
        - **Hypolimnion** - Cold bottom layer
        """)
    
    st.markdown("---")
    st.markdown("### ⚙️ Advanced Settings Guide")
    
    st.markdown("""
    **Early Stopping Patience:**
    - Controls when training stops if no improvement occurs
    - Higher values = more thorough training but slower
    - Recommended: 5-20 iterations
    
    **Validation Split Ratio:**
    - Fraction of data used to validate model performance
    - 0.2 means 80% training, 20% validation
    - Recommended: 0.15-0.25 for most datasets
    
    **Multitask Kernel Rank:**
    - Controls how measurements correlate with each other
    - Rank 1: Simple correlations (faster, less prone to overfitting)
    - Rank 3-5: Complex correlations (slower, needs more data)
    - Recommended: Start with 1, increase if measurements are highly correlated
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Tips & Best Practices")
    
    st.info("""
    **Data Quality:**
    - Ensure GPS coordinates are accurate (num_sats ≥ 4)
    - Cover the lake uniformly with measurements
    - Include measurements at multiple depths
    - Aim for at least 100+ data points for reliable predictions
    
    **Model Performance:**
    - If predictions seem off, try adjusting the kernel rank
    - Check training RMSE vs validation RMSE for overfitting
    - Higher uncertainty in areas with sparse measurements is normal
    
    **Interpretation:**
    - Red shaded areas in depth plots = high uncertainty
    - Thermocline depth varies seasonally (summer: shallow, winter: deep/mixed)
    - Hypoxia typically develops in deep water during summer stratification
    """)
    
    st.markdown("---")
    st.markdown("### 📧 Support")
    st.markdown("""
    For technical support or questions about the dashboard, please contact:
    - **Email:** support@lakewater-dashboard.com
    - **Documentation:** [User Manual](https://docs.lakewater-dashboard.com)
    """)

