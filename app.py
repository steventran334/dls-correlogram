import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Correlogram Analysis", layout="wide")

st.title("📊 Correlogram Scattering Analysis")
st.markdown("""
**Instructions:**
1. Upload your `.xlsx` file.
2. The app will automatically read all sheets (conditions).
3. Select your X-axis (Lag time) and Y-axes (Back, Side, Forward scattering) below.
""")

# --- 1. File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        # Read all sheets at once
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None)
        sheet_names = list(all_sheets.keys())
        
        st.success(f"Loaded {len(sheet_names)} conditions: {', '.join(sheet_names)}")

        if not sheet_names:
            st.error("The uploaded file has no sheets.")
            st.stop()

        # --- 2. Data Mapping (Column Selection) ---
        st.subheader("🛠️ Column Mapping")
        
        # Get columns from the first sheet to populate dropdowns
        first_sheet_name = sheet_names[0]
        sample_df = all_sheets[first_sheet_name]
        all_columns = list(sample_df.columns)

        # Helper to find default column index based on keywords
        def get_default_index(search_terms, columns):
            for i, col in enumerate(columns):
                if any(term in col.lower() for term in search_terms):
                    return i
            return 0

        # Auto-detect columns
        ix_x = get_default_index(["lag", "time", "x"], all_columns)
        ix_back = get_default_index(["back", "135", "backward"], all_columns)
        ix_side = get_default_index(["side", "90"], all_columns)
        ix_fwd = get_default_index(["forw", "fwd", "45", "forward"], all_columns)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            x_col = st.selectbox("X-Axis (Lag Time)", all_columns, index=ix_x)
        with col2:
            back_col = st.selectbox("Back Scattering (Y)", all_columns, index=ix_back)
        with col3:
            side_col = st.selectbox("Side Scattering (Y)", all_columns, index=ix_side)
        with col4:
            fwd_col = st.selectbox("Forward Scattering (Y)", all_columns, index=ix_fwd)

        # --- 3. Plotting Logic ---
        st.markdown("---")
        
        def create_overlay_plot(angle_name, y_column, log_x=True):
            fig = go.Figure()
            
            # Loop through every sheet (condition) and add a trace
            for sheet_name, df in all_sheets.items():
                if x_col in df.columns and y_column in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df[x_col],
                        y=df[y_column],
                        mode='lines',
                        name=sheet_name,
                        opacity=0.8
                    ))
            
            fig.update_layout(
                title=f"<b>{angle_name} Scattering Overlay</b>",
                xaxis_title=x_col,
                yaxis_title="Correlation / Intensity",
                hovermode="x unified",
                template="plotly_white",
                height=500,
                legend=dict(title="Condition")
            )
            
            if log_x:
                fig.update_xaxes(type="log")
                
            return fig

        # --- 4. Display Tabs ---
        tab1, tab2, tab3 = st.tabs(["🔙 Back Scattering", "↔️ Side Scattering", "🔜 Forward Scattering"])

        with tab1:
            log_back = st.checkbox("Log Scale X-Axis", value=True, key="log_back")
            fig_back = create_overlay_plot("Back", back_col, log_back)
            st.plotly_chart(fig_back, use_container_width=True)

        with tab2:
            log_side = st.checkbox("Log Scale X-Axis", value=True, key="log_side")
            fig_side = create_overlay_plot("Side", side_col, log_side)
            st.plotly_chart(fig_side, use_container_width=True)

        with tab3:
            log_fwd = st.checkbox("Log Scale X-Axis", value=True, key="log_fwd")
            fig_fwd = create_overlay_plot("Forward", fwd_col, log_fwd)
            st.plotly_chart(fig_fwd, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.warning("Please ensure your Excel file works correctly.")

else:
    st.info("👆 Upload an Excel file to get started.")
