import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` or `.csv` file. 
2. Select **Conditions** and **Angles**.
3. Use the **Color Customization** section in the sidebar to change the series colors.
""")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Handle file types
        if uploaded_file.name.endswith('.csv'):
            all_sheets = {'Uploaded Data': pd.read_csv(uploaded_file, header=1)}
        else:
            all_sheets = pd.read_excel(uploaded_file, sheet_name=None, header=1)
            
        sheet_names = list(all_sheets.keys())
        
        # --- 2. Data Selectors ---
        st.markdown("### 1️⃣ Select Data")
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_conditions = st.multiselect(
                "Choose Conditions to Plot:",
                sheet_names,
                default=sheet_names[0] if sheet_names else None,
                help="Select sheets/conditions from your file."
            )
        with col_sel2:
            selected_angles = st.multiselect(
                "Choose Angles to View:",
                ["Back", "Side", "Forward"],
                default=["Back", "Side", "Forward"],
                help="Back, Side, and Forward scattering angles."
            )

        if not selected_conditions:
            st.info("👆 Please select at least one condition.")
            st.stop()

        # --- 3. Sidebar Configuration ---
        st.sidebar.header("Graph Settings")
        show_exp_vs_fit = st.sidebar.checkbox("Show 'Exp vs Fit' Comparison", value=True)
        show_residuals = st.sidebar.checkbox("Show Residuals & Error Analysis", value=True)
        use_log_scale = st.sidebar.checkbox("Use Log Scale for X-Axis", value=True)
        
        beta_val = st.sidebar.number_input(
            "Intercept (Beta) for g₂ calc", 
            value=1.0, min_value=0.1, max_value=1.0, step=0.01, 
            help="Used to convert g₁ to g₂. Standard DLS assumes 1.0."
        )

        # --- 4. Color Customization Feature ---
        st.sidebar.markdown("---")
        st.sidebar.header("🎨 Color Customization")
        
        # Create a dictionary to store user-defined colors for each angle
        angle_colors = {}
        default_colors = {"Back": "#0000FF", "Side": "#008000", "Forward": "#FF0000"} # Blue, Green, Red
        
        for angle in ["Back", "Side", "Forward"]:
            angle_colors[angle] = st.sidebar.color_picker(f"Color for {angle}", default_colors[angle])

        # --- 5. Helpers & Logic ---
        line_styles = ['solid', 'dash', 'longdash', 'dashdot', 'dot']
        
        angle_map = {
            "Back":    {'t_exp': 0, 'd_exp': 1, 't_fit': 2, 'd_fit': 3},
            "Side":    {'t_exp': 4, 'd_exp': 5, 't_fit': 6, 'd_fit': 7},
            "Forward": {'t_exp': 8, 'd_exp': 9, 't_fit': 10, 'd_fit': 11}
        }

        def get_column_data(df, time_idx, data_idx):
            if df.shape[1] <= max(time_idx, data_idx):
                return pd.Series(), pd.Series()
            clean_df = df.iloc[:, [time_idx, data_idx]].dropna()
            clean_df = clean_df.apply(pd.to_numeric, errors='coerce').dropna()
            return clean_df.iloc[:, 0], clean_df.iloc[:, 1]

        def get_aligned_data(df, indices, t_min, t_max):
            if df.shape[1] <= max(indices.values()):
                return None, None, None
            cols = [indices['t_exp'], indices['d_exp'], indices['t_fit'], indices['d_fit']]
            subset = df.iloc[:, cols].dropna()
            subset = subset.apply(pd.to_numeric, errors='coerce').dropna()
            time_col = subset.iloc[:, 0]
            mask = (time_col >= t_min) & (time_col <= t_max)
            subset = subset[mask]
            if subset.empty:
                return None, None, None
            return subset.iloc[:, 0], subset.iloc[:, 1], subset.iloc[:, 3]

        def update_axes_layout(fig, y_title="Correlation Coefficient (g₂-1)"):
            axis_type = "log" if use_log_scale else "linear"
            fig.update_xaxes(
                title="Time (µs)", 
                type=axis_type, tickformat=".1e", exponentformat="e",
                showline=True, linewidth=1, linecolor='black', mirror=True,
                zeroline=False
            )
            fig.update_yaxes(
                title=y_title, 
                showline=True, linewidth=1, linecolor='black', mirror=True,
                zeroline=False, rangemode="tozero"
            )
            return fig

        # --- 6. Plotting Functions ---

        def create_single_type_plot(data_type_key, title):
            fig = go.Figure()
            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    style = line_styles[i % len(line_styles)]
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        t_idx = indices['t_exp'] if data_type_key == 'd_exp' else indices['t_fit']
                        d_idx = indices[data_type_key]
                        x_data, y_data = get_column_data(df, t_idx, d_idx)
                        if not x_data.empty:
                            fig.add_trace(go.Scatter(
                                x=x_data, y=y_data, mode='lines',
                                name=f"{sheet_name} - {angle}",
                                line=dict(color=angle_colors[angle], dash=style, width=2),
                                legendgroup=f"{sheet_name}" 
                            ))
            fig.update_layout(title=f"<b>{title}</b>", template="plotly_white", height=500)
            return update_axes_layout(fig)

        def create_comparison_plot():
            fig = go.Figure()
            for sheet_name in selected_conditions:
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        c = angle_colors[angle]
                        x_exp, y_exp = get_column_data(df, indices['t_exp'], indices['d_exp'])
                        if not x_exp.empty:
                            fig.add_trace(go.Scatter(
                                x=x_exp, y=y_exp, mode='lines',
                                name=f"{sheet_name} {angle} (Exp)",
                                line=dict(color=c, dash='dot', width=3),
                                legendgroup=f"{sheet_name}_{angle}"
                            ))
                            x_fit, y_fit = get_column_data(df, indices['t_fit'], indices['d_fit'])
                            fig.add_trace(go.Scatter(
                                x=x_fit, y=y_fit, mode='lines',
                                name=f"{sheet_name} {angle} (Fit)",
                                line=dict(color=c, dash='solid', width=1.5),
                                legendgroup=f"{sheet_name}_{angle}"
                            ))
            fig.update_layout(title="<b>Experimental (Dots) vs Fit (Solid)</b>", template="plotly_white", height=600)
            return update_axes_layout(fig)

        def create_residuals_plot(t_min, t_max):
            fig = go.Figure()
            error_data = []
            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    style = line_styles[i % len(line_styles)]
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        try:
                            t, y_exp, y_fit = get_aligned_data(df, indices, t_min, t_max)
                            if t is None: continue
                            
                            residuals_g1 = y_exp - y_fit
                            g2_exp = 1 + beta_val * (y_exp**2)
                            g2_fit = 1 + beta_val * (y_fit**2)
                            rmse_g2 = np.sqrt(np.mean((g2_exp - g2_fit)**2))
                            
                            error_data.append({
                                "Condition": sheet_name,
                                "Angle": angle,
                                "Specialist Error (RMSE g₂)": f"{rmse_g2:.5f}",
                                "SSD (g₁)": f"{np.sum(residuals_g1**2):.5f}"
                            })

                            fig.add_trace(go.Scatter(
                                x=t, y=residuals_g1,
                                mode='lines',
                                name=f"{sheet_name} {angle}",
                                line=dict(color=angle_colors[angle], dash=style, width=1.5),
                                hovertemplate=f"<b>{sheet_name} {angle}</b><br>Res: %{{y:.2e}}<br>Time: %{{x:.1e}}"
                            ))
                        except:
                            continue 
            fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            fig.update_layout(title="<b>Residuals (Experimental - Fit)</b>", template="plotly_white", height=500)
            return update_axes_layout(fig, y_title="Residuals (g₁)"), pd.DataFrame(error_data)

        # --- 7. Final Layout ---
        st.markdown("### 2️⃣ Visual Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Experimental Data")
            st.plotly_chart(create_single_type_plot('d_exp', "Experimental Data Overlay"), use_container_width=True)
        with col2:
            st.markdown("#### Distribution Fit")
            st.plotly_chart(create_single_type_plot('d_fit', "Distribution Fit Overlay"), use_container_width=True)

        if show_exp_vs_fit:
            st.markdown("---")
            st.markdown("#### Experimental vs. Fit Comparison")
            # Dynamic legend based on chosen colors
            st.info(f"🎨 Legend: <span style='color:{angle_colors['Back']}'>●</span> Back | <span style='color:{angle_colors['Side']}'>●</span> Side | <span style='color:{angle_colors['Forward']}'>●</span> Forward (dotted = exp, solid = fit)", icon="ℹ️")
            st.plotly_chart(create_comparison_plot(), use_container_width=True)

        if show_residuals:
            st.markdown("---")
            st.markdown("### 3️⃣ Fit Quality & Specialist Metrics")
            try:
                sample_df = list(all_sheets.values())[0]
                min_t = float(sample_df.iloc[:, 0].min())
                max_t = float(sample_df.iloc[:, 0].max())
            except:
                min_t, max_t = 0.0, 1000000.0
            
            range_val = st.slider("Select Time Range for Error Calculation (µs)", 
                                  min_value=min_t, max_value=max_t, value=(min_t, max_t), step=1.0)
            
            fig_res, df_error = create_residuals_plot(range_val[0], range_val[1])
            r_col1, r_col2 = st.columns([3, 1])
            with r_col1:
                st.plotly_chart(fig_res, use_container_width=True)
            with r_col2:
                st.markdown("#### Error Metrics")
                st.dataframe(df_error, hide_index=True)
                st.caption("""
                **Specialist Error (RMSE g₂):** Matches Malvern Zetasizer 'Distribution Fit Error'. 
                Acceptable threshold is typically **< 0.005**.
                """)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👆 Please upload an Excel (.xlsx) or CSV file to begin.")
