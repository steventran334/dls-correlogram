import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` file.
2. Select which **Angles** you want to visualize (Back, Side, Forward).
3. The app will generate three graphs for each angle:
    * **Experimental Overlay** (Comparing all sheets)
    * **Fit Overlay** (Comparing all sheets)
    * **Experimental vs. Fit** (Direct comparison)
""")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        # Read all sheets. We use header=1 to skip the first row ("back", "side", etc.)
        # and use the second row ("Time", "Correlation", etc.) as the actual header.
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None, header=1)
        sheet_names = list(all_sheets.keys())
        
        st.success(f"Loaded {len(sheet_names)} conditions: {', '.join(sheet_names)}")

        if not sheet_names:
            st.error("The uploaded file has no sheets.")
            st.stop()

        # --- 2. Sidebar Controls ---
        st.sidebar.header("Graph Settings")
        
        # Multiselect for Angles
        selected_angles = st.sidebar.multiselect(
            "Select Angles to View:",
            ["Back", "Side", "Forward"],
            default=["Back"]
        )

        # Checkbox to toggle the third graph (Exp vs Fit) which can be busy
        show_exp_vs_fit = st.sidebar.checkbox("Show 'Exp vs Fit' Graph", value=True)
        
        # Filter for the 'Exp vs Fit' graph to avoid clutter?
        # If showing all sheets is too messy, user can select specific sheets here.
        selected_sheets_for_fit = st.sidebar.multiselect(
            "Select Conditions for 'Exp vs Fit':",
            sheet_names,
            default=sheet_names
        )

        # --- 3. Plotting Functions ---

        def get_column_data(df, time_idx, data_idx):
            """Helper to safely get time and data columns by index."""
            # Use iloc to access by position (safest for this strict format)
            # Drop NaNs to avoid plotting empty rows
            clean_df = df.iloc[:, [time_idx, data_idx]].dropna()
            return clean_df.iloc[:, 0], clean_df.iloc[:, 1]

        def create_overlay_plot(angle_name, time_col_idx, data_col_idx, title_suffix):
            """Creates a plot overlaying data from ALL sheets."""
            fig = go.Figure()
            for sheet_name, df in all_sheets.items():
                x_data, y_data = get_column_data(df, time_col_idx, data_col_idx)
                
                fig.add_trace(go.Scatter(
                    x=x_data, y=y_data,
                    mode='lines',
                    name=sheet_name,
                    opacity=0.8
                ))
            
            fig.update_layout(
                title=f"<b>{angle_name} - {title_suffix}</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=450,
                xaxis_type="log" # Log scale for Lag Time is standard
            )
            return fig

        def create_exp_vs_fit_plot(angle_name, t_exp_idx, d_exp_idx, t_fit_idx, d_fit_idx):
            """Creates a plot comparing Exp vs Fit for SELECTED sheets."""
            fig = go.Figure()
            
            # Use a color palette to match Exp and Fit for the same sheet
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for i, sheet_name in enumerate(selected_sheets_for_fit):
                df = all_sheets[sheet_name]
                color = colors[i % len(colors)]
                
                # Experimental Data (Solid Line)
                x_exp, y_exp = get_column_data(df, t_exp_idx, d_exp_idx)
                fig.add_trace(go.Scatter(
                    x=x_exp, y=y_exp,
                    mode='lines',
                    name=f"{sheet_name} (Exp)",
                    line=dict(color=color, width=2),
                    legendgroup=sheet_name
                ))

                # Fit Data (Dashed Line)
                x_fit, y_fit = get_column_data(df, t_fit_idx, d_fit_idx)
                fig.add_trace(go.Scatter(
                    x=x_fit, y=y_fit,
                    mode='lines',
                    name=f"{sheet_name} (Fit)",
                    line=dict(color=color, width=2, dash='dot'),
                    legendgroup=sheet_name
                ))

            fig.update_layout(
                title=f"<b>{angle_name} - Experimental vs Distribution Fit</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=500,
                xaxis_type="log"
            )
            return fig

        # --- 4. Main Display Loop ---
        
        # Define Column Indices (0-based)
        # Structure: [Time_Exp, Data_Exp, Time_Fit, Data_Fit]
        # Back: Cols A, B, C, D -> Indices 0, 1, 2, 3
        # Side: Cols E, F, G, H -> Indices 4, 5, 6, 7
        # Fwd:  Cols I, J, K, L -> Indices 8, 9, 10, 11
        
        angle_map = {
            "Back":    {'t_exp': 0, 'd_exp': 1, 't_fit': 2, 'd_fit': 3},
            "Side":    {'t_exp': 4, 'd_exp': 5, 't_fit': 6, 'd_fit': 7},
            "Forward": {'t_exp': 8, 'd_exp': 9, 't_fit': 10, 'd_fit': 11}
        }

        if not selected_angles:
            st.info("👈 Please select at least one angle from the sidebar.")

        for angle in selected_angles:
            indices = angle_map[angle]
            
            st.markdown(f"### 📐 {angle} Scattering Analysis")
            
            # Create Columns for Layout
            c1, c2 = st.columns(2)
            
            with c1:
                # Graph 1: Experimental Data Overlay
                fig1 = create_overlay_plot(angle, indices['t_exp'], indices['d_exp'], "Experimental Data")
                st.plotly_chart(fig1, use_container_width=True)
                
            with c2:
                # Graph 2: Fit Data Overlay
                fig2 = create_overlay_plot(angle, indices['t_fit'], indices['d_fit'], "Distribution Fit")
                st.plotly_chart(fig2, use_container_width=True)

            # Graph 3: Exp vs Fit Overlay (Optional)
            if show_exp_vs_fit:
                st.markdown(f"##### {angle}: Experimental vs. Fit Comparison")
                fig3 = create_exp_vs_fit_plot(angle, indices['t_exp'], indices['d_exp'], indices['t_fit'], indices['d_fit'])
                st.plotly_chart(fig3, use_container_width=True)
            
            st.markdown("---")

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.warning("Ensure your file has the standard structure: Row 1=Headers, Row 2=Units/Names, Row 3+=Data.")
else:
    st.info("👆 Upload an Excel file to get started.")
