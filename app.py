import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` file.
2. **Select Conditions** and **Angles**.
3. All selected data will be overlaid on the graphs below (Conditions = Colors, Angles = Line Styles).
""")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        # Read all sheets. header=1 uses the second row as headers.
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None, header=1)
        sheet_names = list(all_sheets.keys())
        
        # --- 2. Condition Selection ---
        st.markdown("### 1️⃣ Select Data")
        col_sel1, col_sel2 = st.columns(2)
        
        with col_sel1:
            selected_conditions = st.multiselect(
                "Choose Conditions to Plot (Colors):",
                sheet_names,
                default=None, 
                help="Different conditions will be assigned different colors."
            )

        with col_sel2:
            selected_angles = st.multiselect(
                "Choose Angles to Overlay (Line Styles):",
                ["Back", "Side", "Forward"],
                default=["Back"],
                help="Back=Solid, Side=Dash, Forward=Dot"
            )

        if not selected_conditions:
            st.info("👆 Please select at least one condition to generate graphs.")
            st.stop()

        if not selected_angles:
            st.info("👆 Please select at least one angle.")
            st.stop()

        # --- 3. Sidebar Settings ---
        st.sidebar.header("Graph Settings")
        show_exp_vs_fit = st.sidebar.checkbox("Show 'Exp vs Fit' Graph", value=True)
        use_log_scale = st.sidebar.checkbox("Use Log Scale for X-Axis", value=True)

        # --- 4. Plotting Functions ---

        # Define styles for angles to distinguish them on the same graph
        angle_styles = {
            "Back": "solid",
            "Side": "dash",
            "Forward": "dot"
        }

        # Define Index Map
        angle_map = {
            "Back":    {'t_exp': 0, 'd_exp': 1, 't_fit': 2, 'd_fit': 3},
            "Side":    {'t_exp': 4, 'd_exp': 5, 't_fit': 6, 'd_fit': 7},
            "Forward": {'t_exp': 8, 'd_exp': 9, 't_fit': 10, 'd_fit': 11}
        }
        
        # Consistent Color Palette
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        def get_column_data(df, time_idx, data_idx):
            """Helper to safely get time and data columns by index."""
            clean_df = df.iloc[:, [time_idx, data_idx]].dropna()
            clean_df = clean_df.apply(pd.to_numeric, errors='coerce').dropna()
            return clean_df.iloc[:, 0], clean_df.iloc[:, 1]

        def create_multi_angle_plot(data_type_key, title):
            """
            Creates a plot overlaying ALL selected conditions AND angles.
            data_type_key: 'd_exp' or 'd_fit' (to choose which columns to grab)
            """
            fig = go.Figure()
            
            # Loop through Conditions (assigns Color)
            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    color = colors[i % len(colors)]

                    # Loop through Angles (assigns Line Style)
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        
                        # Determine which Time/Data columns to use based on graph type (Exp or Fit)
                        t_idx = indices['t_exp'] if data_type_key == 'd_exp' else indices['t_fit']
                        d_idx = indices[data_type_key]
                        
                        x_data, y_data = get_column_data(df, t_idx, d_idx)
                        
                        # Create Trace
                        fig.add_trace(go.Scatter(
                            x=x_data, y=y_data,
                            mode='lines',
                            name=f"{sheet_name} ({angle})",
                            line=dict(
                                color=color, 
                                dash=angle_styles[angle],
                                width=2
                            ),
                            legendgroup=f"{sheet_name}", # Group by condition in legend
                            hovertemplate=f"<b>{sheet_name} - {angle}</b><br>Time: %{{x:.2e}}<br>Corr: %{{y:.3f}}<extra></extra>"
                        ))
            
            # Formatting
            axis_type = "log" if use_log_scale else "linear"
            fig.update_xaxes(type=axis_type, tickformat=".1e", exponentformat="e")
            
            fig.update_layout(
                title=f"<b>{title}</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=500,
                legend=dict(title="Condition (Angle)")
            )
            return fig

        def create_comparison_plot_all():
            """Creates the messy Exp vs Fit graph for everything selected."""
            fig = go.Figure()
            
            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    color = colors[i % len(colors)]

                    for angle in selected_angles:
                        indices = angle_map[angle]
                        
                        # Experimental (Solid/Dash/Dot based on angle)
                        x_exp, y_exp = get_column_data(df, indices['t_exp'], indices['d_exp'])
                        fig.add_trace(go.Scatter(
                            x=x_exp, y=y_exp,
                            mode='lines',
                            name=f"{sheet_name} {angle} (Exp)",
                            line=dict(color=color, dash=angle_styles[angle], width=2),
                            legendgroup=f"{sheet_name}_{angle}",
                            showlegend=True
                        ))

                        # Fit (Same style but transparent/thinner or maybe markers? 
                        # To distinguish Exp vs Fit AND Angle types is hard. 
                        # Strategy: Fit is always DOTTED? No, that conflicts with Forward.
                        # Strategy: Fit = lighter opacity same style)
                        
                        x_fit, y_fit = get_column_data(df, indices['t_fit'], indices['d_fit'])
                        fig.add_trace(go.Scatter(
                            x=x_fit, y=y_fit,
                            mode='lines',
                            name=f"{sheet_name} {angle} (Fit)",
                            line=dict(color=color, dash=angle_styles[angle], width=1), # Thinner line
                            opacity=0.5, # Lighter
                            legendgroup=f"{sheet_name}_{angle}",
                            showlegend=False
                        ))

            axis_type = "log" if use_log_scale else "linear"
            fig.update_xaxes(type=axis_type, tickformat=".1e", exponentformat="e")
            fig.update_layout(
                title="<b>Experimental vs Fit (Thick=Exp, Thin=Fit)</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=600
            )
            return fig

        # --- 5. Main Display ---

        st.markdown("### 2️⃣ Combined Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. Experimental Data Graph (All angles overlaid)
            st.markdown("#### Experimental Data")
            fig_exp = create_multi_angle_plot('d_exp', "Experimental Data Overlay")
            st.plotly_chart(fig_exp, use_container_width=True)

        with col2:
            # 2. Fit Data Graph (All angles overlaid)
            st.markdown("#### Distribution Fit")
            fig_fit = create_multi_angle_plot('d_fit', "Distribution Fit Overlay")
            st.plotly_chart(fig_fit, use_container_width=True)

        # 3. Comparison Graph
        if show_exp_vs_fit:
            st.markdown("---")
            st.markdown("#### Experimental vs Fit Comparison")
            st.info("💡 Note: Exp data is thick line, Fit data is thin/transparent line.")
            fig_comp = create_comparison_plot_all()
            st.plotly_chart(fig_comp, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.warning("Please ensure your Excel file follows the standard template.")
else:
    st.info("👆 Upload an Excel file to get started.")
