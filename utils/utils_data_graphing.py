# utils_data_graphing.py
import streamlit as st

import os
import pandas as pd
import plotly.express as px
from utils.utils_data_handling import get_selected_properties, enhance_storename_with_gdf

from config.config_constants import (DATA_DICT, DEBUG, 
                    SSDB_REF_COLUMN, DATE_COLUMN,
                    STORENAME_COLUMN,MAX_LABELS_TO_SHOW_ON_GRAPH)


def get_dataframe_from_display_name(display_name):
    """
    Reverse lookup to find dataframe key from display name.
    Returns the session_state key for the dataframe.
    """
    for key, (_filename, disp_name, _data_type) in DATA_DICT.items():
        if disp_name == display_name:
            return key
    return None

def get_filtered_dataframe(display_name, selected_properties):
    """
    Get the dataframe filtered by selected properties.
    """
    # Get the session_state key
    df_key = get_dataframe_from_display_name(display_name)
    
    if df_key is None:
        st.print(f"!!!!WARNING get_dataframe_from_display_name Dataframe not found for display name: {display_name}")
        return None
    
    # Get the full dataframe from session_state
    if df_key not in st.session_state:
        st.print(f"!!!!WARNING get_dataframe_from_display_name Dataframe '{df_key}' not found in session_state")
        return None
    
    df_full = st.session_state[df_key]
    
    # Filter by selected properties
    if selected_properties and SSDB_REF_COLUMN in df_full.columns:
        df_filtered = df_full[df_full[SSDB_REF_COLUMN].isin(selected_properties)]
        return df_filtered
    elif selected_properties:
        st.print(f"!!!!WARNING get_dataframe_from_display_name Column '{SSDB_REF_COLUMN}' not found in {display_name} dataframe")
        return None
    else:
        st.info("No properties selected")
        return None

def interpolate_and_plot(df_selected, 
                         value_col, 
                         display_name,
                         resample_freq='MS',
                         max_labels_to_show=10):
    """
    Interpolate data and create plot with actual and interpolated values.
    """
    if DEBUG:
            print(f'$$$$DEBUG interpolate_and_plot df_selected:')
            print(f'{df_selected.columns.tolist()}')
            print(f'{df_selected.head(10)}')


    if df_selected is None or df_selected.empty:
        st.warning(f"interpolate_and_plot: No data to display")
        return None, None, None, None

    # Improve / correct storename with the storename values from the ssdb
    df_selected = enhance_storename_with_gdf(df_selected)

    # Raw data expander
    if DEBUG:
        with st.expander("View selected data"):
            st.dataframe(df_selected[df_selected.ssdb_ref==2741], hide_index=True, width='stretch')
            try:
                strFpathtest = r'C:\Users\paul.bennathan\OneDrive - Savills plc\WIP\SS_Data_Indices\Data_indices\Output\Streamlit_Test_Outputs'
                df_selected.to_csv(os.path.join(strFpathtest, 'df_selected_test.csv'), index=False)
                print(f'$$$$DEBUG - saved df_selected')
            except:
                print(f'$$$$DEBUG - could not save df_selected')

    df_interpol = df_selected.copy()

    if DEBUG:
        print(f"$$$$DEBUG: interpolate_and_plot df_interpol before sorting: {df_interpol.shape}")
        print(f"{df_interpol.head(10)}")

    
    # Sort values
    df_interpol = df_interpol.sort_values(by=[SSDB_REF_COLUMN, DATE_COLUMN], ascending=[True, True])
    
    if DEBUG:
        print(f"$$$$DEBUG: interpolate_and_plot df_interpol before resample: {df_interpol.shape}")
        print(f"{df_interpol.head(10)}")
    
    # Resample monthly
    df_interpol_resample = (df_interpol.set_index(DATE_COLUMN)
                           .groupby(SSDB_REF_COLUMN)
                           .resample(resample_freq)
                           .asfreq()
                           .reset_index())
    
    # Fill storename
    if STORENAME_COLUMN in df_interpol_resample.columns:
        if DEBUG:
            print(f'$$$$DEBUG interpolate_and_plot:')
            print(f'Found STORENAME_COLUMN in df_interpol_resample')
            print(f'{df_interpol_resample.columns.tolist()}')
            print(f'{df_interpol_resample.head(3)}')
        df_interpol_resample[STORENAME_COLUMN] = (df_interpol_resample.groupby(SSDB_REF_COLUMN)[STORENAME_COLUMN]
                                              .transform('last'))
    
    if DEBUG:
        print(f"$$$$DEBUG: interpolate_and_plot df_interpol_resample after resample: {df_interpol_resample.shape}")
        print(df_interpol_resample.head(3))

    
    # Interpolate (limit_area='inside' prevents extrapolation)
    value_col_interp = f'{value_col}_interp'
    df_interpol_resample[value_col_interp] = (df_interpol_resample.groupby(SSDB_REF_COLUMN)[value_col]
                                             .transform(lambda x: x.interpolate(method='linear', limit_area='inside')))
    
    if DEBUG:
        print(f"$$$$DEBUG: interpolate_and_plot df_interpol_resample after interpolation: {df_interpol_resample.shape}")
        print(df_interpol_resample.head(3))
    
    # Get date range for feedback
    min_date = df_interpol_resample[DATE_COLUMN].min()
    max_date = df_interpol_resample[DATE_COLUMN].max()
    
    # Get unique store names count
    color_column = STORENAME_COLUMN if STORENAME_COLUMN in df_interpol_resample.columns else SSDB_REF_COLUMN
    unique_stores = df_interpol_resample[color_column].nunique()
    
    # Determine if legend should be shown
    show_legend = unique_stores <= max_labels_to_show
    
    # Create plot
    fig = px.line(df_interpol_resample, x=DATE_COLUMN, y=value_col_interp, 
                  color=color_column,
                  # title=f"Interpolated {display_name} over Time",
                  hover_data={STORENAME_COLUMN: True})
    
    # Customize hover template
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                      "Date: %{x|%Y-%m-%d}<br>" +
                      f"{display_name}: %{{y:.2f}}<br>" +
                      "<extra></extra>"
    )
    
    # Add markers for actual values
    df_actual = df_interpol_resample[df_interpol_resample[value_col].notna()]
    if not df_actual.empty:
        storename_col = STORENAME_COLUMN if STORENAME_COLUMN in df_actual.columns else SSDB_REF_COLUMN
        customdata = df_actual[storename_col].values
        
        fig.add_scatter(x=df_actual[DATE_COLUMN], y=df_actual[value_col], 
                    mode='markers', name='Actual',
                    marker=dict(color='blue', size=6),
                    customdata=customdata,
                    hovertemplate="<b>Actual</b><br>" +
                                    "<b>%{customdata}</b><br>" +
                                    "Date: %{x|%Y-%m-%d}<br>" +
                                    f"{display_name}: %{{y:.2f}}<br>" +
                                    "<extra></extra>")

    # Add markers for interpolated values
    df_interp_only = df_interpol_resample[df_interpol_resample[value_col].isna()]
    if not df_interp_only.empty:
        storename_col = STORENAME_COLUMN if STORENAME_COLUMN in df_interp_only.columns else SSDB_REF_COLUMN
        customdata = df_interp_only[storename_col].values
        
        fig.add_scatter(x=df_interp_only[DATE_COLUMN], y=df_interp_only[value_col_interp], 
                    mode='markers', name='Interpolated',
                    marker=dict(color='red', size=6, symbol='x'),
                    customdata=customdata,
                    hovertemplate="<b>Interpolated</b><br>" +
                                    "<b>%{customdata}</b><br>" +
                                    "Date: %{x|%Y-%m-%d}<br>" +
                                    f"{display_name}: %{{y:.2f}}<br>" +
                                    "<extra></extra>")
    
    # Configure layout
    legend_config = {
        "orientation": "h",
        "yanchor": "top",
        "y": -0.2,
        "xanchor": "center",
        "x": 0.5
    }
    
    if not show_legend:
        legend_config = None
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title=display_name,
        hovermode='closest',
        showlegend=show_legend,
        legend=legend_config
    )
    
    if not show_legend:
        fig.add_annotation(
            text=f"({unique_stores} stores - legend hidden due to too many stores)",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,  # Moved further down
            showarrow=False,
            font=dict(size=10, color="gray"),
            yshift=-10  # Additional shift in pixels
        )
    
    # Also adjust layout to make room
    fig.update_layout(
        margin=dict(b=50)  # Add bottom margin
    )
    
    # Return all values including legend_hidden and unique_stores
    return fig, df_interpol_resample, min_date, max_date, not show_legend, unique_stores

def display_data_graph(selected_view_display_name, selected_properties, value_col):
    """
    Main function to display the graph for selected data view with two tabs.
    """

    # Get filtered dataframe
    df_filtered = get_filtered_dataframe(selected_view_display_name, selected_properties)
    
    if df_filtered is None or df_filtered.empty:
        st.warning(f"No data available for the selected properties in {selected_view_display_name}")
        return

   
    # Check required columns
    if DATE_COLUMN not in df_filtered.columns:
        st.error("Date column not found in data")
        return
    
    if value_col not in df_filtered.columns:
        st.error(f"Value column '{value_col}' not found in data")
        return
    
    # Interpolate and plot
    result = interpolate_and_plot(df_filtered, value_col=value_col, display_name=selected_view_display_name)
    
    if result[0] is None:
        return
    
    fig, df_interpolated, min_date, max_date, legend_hidden, unique_stores = result
    
    # Add range slider to the figure
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    # Create tabs - fixed headers with scrollable content below
    tab_all_data, tab_average = st.tabs(["📈 All Data", "📊 Average Growth Analysis"])
    
    # Tab 1: All Data (original view)
    with tab_all_data:
        plot_key = f"plot_{value_col}_{'_'.join(str(p) for p in selected_properties[:5])}"
        
        # Date range display
        date_range_container = st.empty()
        range_key = f"{plot_key}_date_range"
        
        if range_key not in st.session_state:
            st.session_state[range_key] = (min_date, max_date)
        
        # Display plot
        st.plotly_chart(fig, width='content', key=plot_key)
        
        # Show caption if legend hidden
        if legend_hidden:
            st.caption(f"ℹ️ {unique_stores} stores - legend hidden due to many stores")
        

        st.caption(f"📊 Total stores in view: {unique_stores}")
        
        # Raw data expander
        with st.expander("View interpolated data"):
            st.dataframe(df_interpolated, hide_index=True, width='stretch')
            if DEBUG:
                try:
                    strFpathtest = r'C:\Users\paul.bennathan\OneDrive - Savills plc\WIP\SS_Data_Indices\Data_indices\Output\Streamlit_Test_Outputs'
                    df_interpolated.to_csv(os.path.join(strFpathtest, 'df_interpolated_test.csv'), index=False)
                    print(f'$$$$DEBUG - saved df_interpolated')
                except:
                    print(f'$$$$DEBUG - could not save: df_interpolated')
    
    # Tab 2: Average Growth Analysis
    with tab_average:
        display_growth_analysis(df_interpolated, value_col, selected_view_display_name)

def display_growth_analysis(df_interpolated, value_col, display_name):
    """
    Display growth analysis with average, highest, and lowest growth.
    """
    
    # Get unique year-month combinations
    dates = df_interpolated[DATE_COLUMN].dt.to_period('M').unique()
    month_options = sorted([d.strftime('%Y-%m') for d in dates])

    col1, col2 = st.columns(2)
    with col1:
        start_month = st.selectbox(
            "Start Month",
            options=month_options,
            index=0,
            key=f"growth_start_{value_col}"
        )
    with col2:
        end_month = st.selectbox(
            "End Month",
            options=month_options,
            index=len(month_options) - 1,
            key=f"growth_end_{value_col}"
        )

    # Convert to datetime (first day of month)
    start_date = pd.to_datetime(start_month)
    end_date = pd.to_datetime(end_month)
    
    if start_date >= end_date:
        st.error("End date must be after start date")
        return

    # Calculate start and end values for each store
    storename_col = STORENAME_COLUMN if STORENAME_COLUMN in df_interpolated.columns else SSDB_REF_COLUMN

    # Get count of properties with data in the selected date range
    properties_with_data = df_interpolated[
        (df_interpolated[DATE_COLUMN] >= pd.to_datetime(start_date)) & 
        (df_interpolated[DATE_COLUMN] <= pd.to_datetime(end_date))
                    ][storename_col].nunique()

    st.caption(f"📊 Properties included in analysis: {properties_with_data}")

    
    # Get values at start and end dates (closest available)
    start_values = df_interpolated[df_interpolated[DATE_COLUMN] <= pd.to_datetime(start_date)] \
        .groupby(storename_col).last().reset_index()[[storename_col, value_col]]
    start_values.columns = [storename_col, f'start_value']
    
    end_values = df_interpolated[df_interpolated[DATE_COLUMN] <= pd.to_datetime(end_date)] \
        .groupby(storename_col).last().reset_index()[[storename_col, value_col]]
    end_values.columns = [storename_col, f'end_value']
    
    # Merge and calculate growth
    growth_df = start_values.merge(end_values, on=storename_col)
    growth_df['growth'] = growth_df['end_value'] - growth_df['start_value']
    growth_df['growth_pct'] = (growth_df['growth'] / growth_df['start_value']) * 100
    
    # Calculate average growth
    avg_growth = growth_df['growth'].mean()
    avg_growth_pct = growth_df['growth_pct'].mean()
    
    # Find highest and lowest growth
    highest_growth = growth_df.loc[growth_df['growth'].idxmax()]
    lowest_growth = growth_df.loc[growth_df['growth'].idxmin()]
    
    # Format numbers with thousand commas and 2dp
    def format_metric(value):
        return f"{value:,.2f}"
    
    # Display summary metrics in order: Lowest / Average / Highest
    st.subheader("Summary Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lowest Growth", format_metric(lowest_growth['growth']), 
                  delta=f"{lowest_growth['growth_pct']:.1f}%", 
                  delta_color="inverse")
    with col2:
        st.metric("Average Growth", format_metric(avg_growth), 
                  delta=f"{avg_growth_pct:.1f}%")
    with col3:
        st.metric("Highest Growth", format_metric(highest_growth['growth']), 
                  delta=f"{highest_growth['growth_pct']:.1f}%", 
                  delta_color="normal")
    
    st.divider()
    
    # Prepare data for plotting in order: Lowest / Average / Highest
    plot_data = []
    
    # Add lowest growth store
    plot_data.append({
        'store': f"Lowest: {lowest_growth[storename_col]}",
        'start_value': lowest_growth['start_value'],
        'end_value': lowest_growth['end_value'],
        'growth': lowest_growth['growth']
    })
    
    # Add average
    plot_data.append({
        'store': 'Average',
        'start_value': growth_df['start_value'].mean(),
        'end_value': growth_df['end_value'].mean(),
        'growth': avg_growth
    })
    
    # Add highest growth store
    plot_data.append({
        'store': f"Highest: {highest_growth[storename_col]}",
        'start_value': highest_growth['start_value'],
        'end_value': highest_growth['end_value'],
        'growth': highest_growth['growth']
    })
    
    plot_df = pd.DataFrame(plot_data)
    


    # Create bar chart with formatted labels
    # Format dates as "Month Year" (e.g., "January 2024")
    start_formatted = start_date.strftime('%B %Y')
    end_formatted = end_date.strftime('%B %Y')
    
    fig_growth = px.bar(
        plot_df, 
        x='store', 
        y='growth',
        title=f"Growth Comparison: {display_name} ({start_formatted} to {end_formatted})",
        text='growth',
        color='store',
        color_discrete_sequence=['red', 'gray', 'green']
    )
    
    # Format bar chart labels with thousand commas and 2dp
    fig_growth.update_traces(
        texttemplate='%{text:,.2f}', 
        textposition='outside'
    )
    fig_growth.update_layout(
        yaxis_title=f"Growth in {display_name}",
        xaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig_growth, width='content')
    
    # Create line chart showing start and end points
    progression_data = []
    for _, row in plot_df.iterrows():
        progression_data.append({'store': row['store'], 'date': start_date.strftime('%Y-%m-%d'), 'value': row['start_value']})
        progression_data.append({'store': row['store'], 'date': end_date.strftime('%Y-%m-%d'), 'value': row['end_value']})
    
    progression_df = pd.DataFrame(progression_data)
    
    fig_progression = px.line(
        progression_df,
        x='date',
        y='value',
        color='store',
        title=f"Value Progression: {display_name}",
        markers=True,
        color_discrete_sequence=['red', 'gray', 'green']
    )
    
    # Position legend low and center, remove x-axis label
    fig_progression.update_layout(
        yaxis_title=display_name,
        xaxis_title="",  # Remove x-axis label
        legend=dict(
            orientation="h",  # Horizontal
            yanchor="top",
            y=-0.2,  # Position below the plot (low)
            xanchor="center",
            x=0.5  # Center horizontally
        )
    )
    
    st.plotly_chart(fig_progression, width='content')
    
    # Display detailed table ordered by Growth % high to low
    display_growth_df = growth_df.copy()
    display_growth_df['growth_pct'] = display_growth_df['growth_pct'].round(1)
    display_growth_df['growth'] = display_growth_df['growth'].round(2)
    display_growth_df['start_value'] = display_growth_df['start_value'].round(2)
    display_growth_df['end_value'] = display_growth_df['end_value'].round(2)
    
    # Sort by Growth % high to low
    display_growth_df = display_growth_df.sort_values('growth_pct', ascending=False)
    display_growth_df.columns = ['Store', 'Start Value', 'End Value', 'Growth', 'Growth %']
    
    st.subheader("Detailed Store Growth")
    # Configure column formatting with centered alignment
    column_config = {
        "Store": st.column_config.TextColumn("Store", width="medium"),
        "Start Value": st.column_config.NumberColumn("Start Value", format="%,.2f"),  # Added comma
        "End Value": st.column_config.NumberColumn("End Value", format="%,.2f"),      # Added comma
        "Growth": st.column_config.NumberColumn("Growth", format="%,.2f"),            # Added comma
        "Growth %": st.column_config.NumberColumn("Growth %", format="%,.1f%%")       # Added comma
    }

    st.dataframe(
        display_growth_df, 
        width='stretch', 
        hide_index=True,
        column_config=column_config
    )

   