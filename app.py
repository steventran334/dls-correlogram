import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` file.
2. Select **Conditions** (different line styles in individual graphs).
3. Select **Angles** (Blue=Back, Green=Side, Red=Forward).
""")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        # Read all sheets
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None, header=1)
        sheet_names = list(all_sheets.keys())
        
        # --- 2. Selectors ---
        st.markdown("### 1️⃣ Select Data")
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_conditions = st.multiselect(
                "Choose Conditions to Plot:",
                sheet_names,
                default=None,
                help="Select sheets. In the separate Exp/Fit graphs, these will use different dash styles."
            )
        with col_sel2:
            selected_angles = st.multiselect(
                "Choose Angles to View:",
                ["Back", "Side", "Forward"],
                default=["Back", "Side", "Forward"],
                help="Back=Blue, Side=Green, Forward=Red"
            )

        if not selected_conditions:
            st.info("👆 Please select at least one condition.")
            st.stop()

        # Sidebar Options
        st.sidebar.header("Graph Settings")
        show_exp_vs_fit = st.sidebar.checkbox("Show 'Exp vs Fit' Comparison", value=True)
        use_log_scale = st.sidebar.checkbox("Use Log Scale for X-Axis", value=True)

        # --- 3. Configuration & Helpers ---

        # 1. Color Map (Fixed by Angle)
        angle_colors = {
            "Back": "blue",
            "Side": "green",
            "Forward": "red"
        }

        # 2. Line Style Map (Cycle for Conditions)
        line_styles = ['solid', 'dash', 'longdash', 'dashdot', 'dot']
        
        # 3. Column Indices
        angle_map = {
            "Back":    {'t_exp': 0, 'd_exp': 1, 't_fit': 2, 'd_fit': 3},
            "Side":    {'t_exp': 4, 'd_exp': 5, 't_fit': 6, 'd_fit': 7},
            "Forward": {'t_exp': 8, 'd_exp': 9, 't_fit': 10, 'd_fit': 11}
        }

        def get_column_data(df, time_idx, data_idx):
            clean_df = df.iloc[:, [time_idx, data_idx]].dropna()
            clean_df = clean_df.apply(pd.to_numeric, errors='coerce').dropna()
            return clean_df.iloc[:, 0], clean_df.iloc[:, 1]

        def update_axes_layout(fig):
            """Helper to apply standard axis styling."""
            axis_type = "log" if use_log_scale else "linear"
            
            fig.update_xaxes(
                type=axis_type, 
                tickformat=".1e", 
                exponentformat="e",
                showline=True, linewidth=1, linecolor='black', mirror=True, # Axis border
                zeroline=False # No internal zero line
            )
            fig.update_yaxes(
                showline=True, linewidth=1, linecolor='black', mirror=True, # Axis border
                zeroline=False,    # REMOVED: The black line crossing the graph
                rangemode="tozero" # ADDED: Forces the axis to go down to 0 so the label shows
            )
            return fig

        # --- 4. Plotting Functions ---

        def create_single_type_plot(data_type_key, title):
            """
            Plots Exp OR Fit data.
            Color = Angle
            Line Style = Condition
            """
            fig = go.Figure()

            # Loop through selected conditions
            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    # Cycle styles for conditions
                    style = line_styles[i % len(line_styles)]
                    
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        
                        # Get Data
                        t_idx = indices['t_exp'] if data_type_key == 'd_exp' else indices['t_fit']
                        d_idx = indices[data_type_key]
                        x_data, y_data = get_column_data(df, t_idx, d_idx)
                        
                        # Plot
                        fig.add_trace(go.Scatter(
                            x=x_data, y=y_data,
                            mode='lines',
                            name=f"{sheet_name} - {angle}",
                            line=dict(
                                color=angle_colors[angle],
                                dash=style,
                                width=2
                            ),
                            legendgroup=f"{sheet_name}" 
                        ))
            
            # Layout
            fig.update_layout(
                title=f"<b>{title}</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=500,
                legend=dict(title="Condition / Angle")
            )
            fig = update_axes_layout(fig)
            return fig

        def create_comparison_plot():
            """
            Plots Exp vs Fit.
            Color = Angle (Blue/Green/Red)
            Line Style = Exp is DOT, Fit is SOLID
            """
            fig = go.Figure()

            for sheet_name in selected_conditions:
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        c = angle_colors[angle]

                        # 1. Experimental Data (Dotted)
                        x_exp, y_exp = get_column_data(df, indices['t_exp'], indices['d_exp'])
                        fig.add_trace(go.Scatter(
                            x=x_exp, y=y_exp,
                            mode='lines',
                            name=f"{sheet_name} {angle} (Exp)",
                            line=dict(color=c, dash='dot', width=3),
                            legendgroup=f"{sheet_name}_{angle}"
                        ))

                        # 2. Fit Data (Solid)
                        x_fit, y_fit = get_column_data(df, indices['t_fit'], indices['d_fit'])
                        fig.add_trace(go.Scatter(
                            x=x_fit, y=y_fit,
                            mode='lines',
                            name=f"{sheet_name} {angle} (Fit)",
                            line=dict(color=c, dash='solid', width=1.5),
                            legendgroup=f"{sheet_name}_{angle}"
                        ))

            fig.update_layout(
                title="<b>Experimental (Dots) vs Fit (Solid)</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=600
            )
            fig = update_axes_layout(fig)
            return fig

        # --- 5. Main Layout ---
        st.markdown("### 2️⃣ Visual Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Experimental Data")
            fig_exp = create_single_type_plot('d_exp', "Experimental Data Overlay")
            st.plotly_chart(fig_exp, use_container_width=True)
        
        with col2:
            st.markdown("#### Distribution Fit")
            fig_fit = create_single_type_plot('d_fit', "Distribution Fit Overlay")
            st.plotly_chart(fig_fit, use_container_width=True)

        if show_exp_vs_fit:
            st.markdown("---")
            st.markdown("#### Experimental vs. Fit Comparison")
            st.info("🔵 Back | 🟢 Side | 🔴 Forward  ---  (dotted = experimental, solid = fit)")
            fig_comp = create_comparison_plot()
            st.plotly_chart(fig_comp, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👆 Upload an Excel file to get started.")
