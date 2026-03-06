import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` file.
2. Select **Conditions** and **Angles**.
3. Scroll down to see **Fit Error Analysis** and **Residuals**.
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
        show_residuals = st.sidebar.checkbox("Show Residuals & Error", value=True)
        use_log_scale = st.sidebar.checkbox("Use Log Scale for X-Axis", value=True)

        # --- 3. Configuration & Helpers ---

        angle_colors = {"Back": "blue", "Side": "green", "Forward": "red"}
        line_styles = ['solid', 'dash', 'longdash', 'dashdot', 'dot']
        
        angle_map = {
            "Back":    {'t_exp': 0, 'd_exp': 1, 't_fit': 2, 'd_fit': 3},
            "Side":    {'t_exp': 4, 'd_exp': 5, 't_fit': 6, 'd_fit': 7},
            "Forward": {'t_exp': 8, 'd_exp': 9, 't_fit': 10, 'd_fit': 11}
        }

        def get_column_data(df, time_idx, data_idx):
            clean_df = df.iloc[:, [time_idx, data_idx]].dropna()
            clean_df = clean_df.apply(pd.to_numeric, errors='coerce').dropna()
            return clean_df.iloc[:, 0], clean_df.iloc[:, 1]

        def get_aligned_data(df, indices):
            cols = [indices['t_exp'], indices['d_exp'], indices['t_fit'], indices['d_fit']]
            subset = df.iloc[:, cols].dropna()
            subset = subset.apply(pd.to_numeric, errors='coerce').dropna()
            return subset.iloc[:, 0], subset.iloc[:, 1], subset.iloc[:, 3]

        def update_axes_layout(fig, y_title="Correlation Coefficient (g₂-1)"):
            axis_type = "log" if use_log_scale else "linear"
            fig.update_xaxes(
                title="Time (µs)", # Updated Label
                type=axis_type, tickformat=".1e", exponentformat="e",
                showline=True, linewidth=1, linecolor='black', mirror=True
            )
            fig.update_yaxes(
                title=y_title, # Updated Label
                showline=True, linewidth=1, linecolor='black', mirror=True,
                zeroline=False, rangemode="tozero"
            )
            return fig

        # --- 4. Plotting Functions ---

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

        def create_residuals_plot():
            fig = go.Figure()
            error_data = []

            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    style = line_styles[i % len(line_styles)]
                    
                    for angle in selected_angles:
                        indices = angle_map[angle]
                        try:
                            t, y_exp, y_fit = get_aligned_data(df, indices)
                            residuals = y_exp - y_fit
                            ssd = np.sum(residuals ** 2)
                            
                            error_data.append({
                                "Condition": sheet_name,
                                "Angle": angle,
                                "Total Fit Error (SSD)": f"{ssd:.6f}"
                            })

                            fig.add_trace(go.Scatter(
                                x=t, y=residuals,
                                mode='lines',
                                name=f"{sheet_name} {angle}",
                                line=dict(color=angle_colors[angle], dash=style, width=1.5),
                                hovertemplate=f"<b>{sheet_name} {angle}</b><br>Res: %{{y:.2e}}<br>Time: %{{x:.1e}}"
                            ))
                        except Exception:
                            continue 

            fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)

            fig.update_layout(title="<b>Residuals (Experimental - Fit)</b>", template="plotly_white", height=500)
            # For residuals, the Y-axis is technically the difference in correlation
            return update_axes_layout(fig, y_title="Residuals (g₂-1)"), pd.DataFrame(error_data)

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

        if show_residuals:
            st.markdown("---")
            st.markdown("### 3️⃣ Fit Quality & Residuals")
            
            fig_res, df_error = create_residuals_plot()
            
            r_col1, r_col2 = st.columns([3, 1])
            
            with r_col1:
                st.plotly_chart(fig_res, use_container_width=True)
            
            with r_col2:
                st.markdown("#### Fit Error (SSD)")
                st.dataframe(df_error, hide_index=True)
                st.caption("SSD = Sum of Squared Differences $\sum(Exp - Fit)^2$")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👆 Upload an Excel file to get started.")
