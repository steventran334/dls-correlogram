import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` file.
2. **Select the Conditions** you want to plot from the dropdown.
3. Choose the **Scattering Angles** (Back, Side, Forward) to visualize.
""")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        # Read all sheets. header=1 uses the second row as headers.
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None, header=1)
        sheet_names = list(all_sheets.keys())
        
        # --- 2. Condition Selection (New Feature) ---
        st.markdown("### 1️⃣ Select Data")
        selected_conditions = st.multiselect(
            "Choose Conditions to Plot:",
            sheet_names,
            default=None, # Start empty so user chooses
            help="Select one or more sheets to overlay on the graphs."
        )

        if not selected_conditions:
            st.info("👆 Please select at least one condition to generate graphs.")
            st.stop()

        # --- 3. Sidebar Settings ---
        st.sidebar.header("Graph Settings")
        
        # Multiselect for Angles
        selected_angles = st.sidebar.multiselect(
            "Select Angles to View:",
            ["Back", "Side", "Forward"],
            default=["Back", "Side", "Forward"]
        )

        # Toggle for the comparison graph
        show_exp_vs_fit = st.sidebar.checkbox("Show 'Exp vs Fit' Graph", value=True)
        
        # Toggle for Log Scale
        use_log_scale = st.sidebar.checkbox("Use Log Scale for X-Axis", value=True)

        # --- 4. Plotting Functions ---

        def get_column_data(df, time_idx, data_idx):
            """Helper to safely get time and data columns by index."""
            # Select columns by index (iloc) to be robust against header name changes
            # Drop NaNs to prevent plotting empty gaps
            clean_df = df.iloc[:, [time_idx, data_idx]].dropna()
            
            # Ensure data is numeric
            clean_df = clean_df.apply(pd.to_numeric, errors='coerce').dropna()
            
            return clean_df.iloc[:, 0], clean_df.iloc[:, 1]

        def create_overlay_plot(angle_name, time_col_idx, data_col_idx, title_suffix):
            """Creates a plot overlaying data from SELECTED sheets only."""
            fig = go.Figure()
            
            # Iterate only through the USER SELECTED conditions
            for sheet_name in selected_conditions:
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    x_data, y_data = get_column_data(df, time_col_idx, data_col_idx)
                    
                    fig.add_trace(go.Scatter(
                        x=x_data, y=y_data,
                        mode='lines',
                        name=sheet_name,
                        opacity=0.8
                    ))
            
            # Update Layout with Scientific Notation
            fig.update_layout(
                title=f"<b>{angle_name} - {title_suffix}</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=450,
                legend=dict(title="Condition")
            )

            # Axis formatting
            axis_type = "log" if use_log_scale else "linear"
            fig.update_xaxes(type=axis_type, tickformat=".1e", exponentformat="e") 
            
            return fig

        def create_comparison_plot(angle_name, indices):
            """Creates Exp vs Fit comparison for SELECTED sheets."""
            fig = go.Figure()
            
            # Distinct colors for different sheets
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            
            for i, sheet_name in enumerate(selected_conditions):
                if sheet_name in all_sheets:
                    df = all_sheets[sheet_name]
                    color = colors[i % len(colors)]
                    
                    # Exp Data (Solid)
                    x_exp, y_exp = get_column_data(df, indices['t_exp'], indices['d_exp'])
                    fig.add_trace(go.Scatter(
                        x=x_exp, y=y_exp,
                        mode='lines',
                        name=f"{sheet_name} (Exp)",
                        line=dict(color=color, width=2),
                        legendgroup=sheet_name
                    ))

                    # Fit Data (Dash)
                    x_fit, y_fit = get_column_data(df, indices['t_fit'], indices['d_fit'])
                    fig.add_trace(go.Scatter(
                        x=x_fit, y=y_fit,
                        mode='lines',
                        name=f"{sheet_name} (Fit)",
                        line=dict(color=color, width=2, dash='dot'),
                        legendgroup=sheet_name,
                        showlegend=False # Hide duplicate legend entry if desired, or keep True
                    ))

            fig.update_layout(
                title=f"<b>{angle_name} - Experimental vs Fit Comparison</b>",
                xaxis_title="Time (µs)",
                yaxis_title="Correlation",
                template="plotly_white",
                height=500
            )
            
            # Axis formatting
            axis_type = "log" if use_log_scale else "linear"
            fig.update_xaxes(type=axis_type, tickformat=".1e", exponentformat="e")

            return fig

        # --- 5. Main Display Logic ---
        
        # Column Index Map based on your file structure
        # Back: Cols A,B (Exp) & C,D (Fit) -> Indices 0,1 & 2,3
        angle_map = {
            "Back":    {'t_exp': 0, 'd_exp': 1, 't_fit': 2, 'd_fit': 3},
            "Side":    {'t_exp': 4, 'd_exp': 5, 't_fit': 6, 'd_fit': 7},
            "Forward": {'t_exp': 8, 'd_exp': 9, 't_fit': 10, 'd_fit': 11}
        }

        st.markdown("### 2️⃣ Analyze Scatter Angles")

        for angle in selected_angles:
            indices = angle_map[angle]
            
            st.markdown(f"#### 📐 {angle} Scattering")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Experimental Data Graph
                fig_exp = create_overlay_plot(angle, indices['t_exp'], indices['d_exp'], "Experimental Data")
                st.plotly_chart(fig_exp, use_container_width=True)
                
            with col2:
                # Distribution Fit Graph
                fig_fit = create_overlay_plot(angle, indices['t_fit'], indices['d_fit'], "Distribution Fit")
                st.plotly_chart(fig_fit, use_container_width=True)

            # Comparison Graph
            if show_exp_vs_fit:
                fig_comp = create_comparison_plot(angle, indices)
                st.plotly_chart(fig_comp, use_container_width=True)
            
            st.markdown("---")

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.warning("Please ensure your Excel file follows the standard template.")
else:
    st.info("👆 Upload an Excel file to get started.")
