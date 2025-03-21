import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import altair as alt
import streamlit_shadcn_ui as ui
from utils.vdx_data import get_vdx_data, get_quality_mapping, get_quality_percent


def get_video_calls_quality():
    col_1 = st.columns([1])[0]

    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Kvalitet', tag='Kvalitet'),
        ], color='dark', size='md', position='top', align='start', use_container_width=True)

    try:
        if 'vdx_data' not in st.session_state:
            with st.spinner('Loading data...'):
                vdx_data = get_vdx_data()
                if not vdx_data.empty:
                    st.session_state.vdx_data = vdx_data
                else:
                    return

        vdx_data = st.session_state.vdx_data
        vdx_data['start_time'] = pd.to_datetime(vdx_data['start_time'])
        vdx_data['Year'] = vdx_data['start_time'].dt.year
        vdx_data['Month'] = vdx_data['start_time'].dt.month
        vdx_data['Månedsdag'] = vdx_data['start_time'].dt.day.astype(int)

        month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}

        unique_years = sorted(vdx_data['Year'].unique(), reverse=True)

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "Vælg et år",
                unique_years,
                format_func=lambda x: f'{x}',
                index=unique_years.tolist().index(st.session_state['selected_year']) if 'selected_year' in st.session_state and st.session_state['selected_year'] is not None else 0,
                key='year_select',
                help="Vælg det år, for hvilket du vil se dataene."
            )
        with col2:
            filtered_result_year = vdx_data[vdx_data['Year'] == selected_year]
            unique_months = filtered_result_year['Month'].sort_values().unique()
            selected_month = st.selectbox('Vælg en måned', unique_months, format_func=lambda x: month_names[x], help="Vælg den måned, for hvilken du vil se dataene.")

        filtered_data = filtered_result_year[filtered_result_year['Month'] == selected_month]

        filtered_data['overall_quality'] = filtered_data['overall_quality'].map(get_quality_mapping())

        if content_tabs == 'Kvalitet':
            overall_quality_summary = filtered_data.groupby('overall_quality').size().reset_index(name='Antal møder')
            overall_quality_summary['overall_quality_percent'] = (overall_quality_summary['Antal møder'] / overall_quality_summary['Antal møder'].sum()) * 100

            st.write("## Samlet Kvalitet af VDX Møder")

            col1, col2, col3 = st.columns(3)

            with col1:
                ui.metric_card(title="Høj Kvalitet", content=f"{get_quality_percent(overall_quality_summary, 'God'):.2f}%", description="Procent af møder med høj kvalitet.")
            with col2:
                ui.metric_card(title="Middel Kvalitet", content=f"{get_quality_percent(overall_quality_summary, 'Ok'):.2f}%", description="Procent af møder med middel kvalitet.")
            with col3:
                ui.metric_card(title="Ukendt Kvalitet", content=f"{get_quality_percent(overall_quality_summary, 'Ukendt'):.2f}%", description="Procent af møder med ukendt kvalitet.")

            col1, col2 = st.columns(2)

            with col1:
                quality_chart = alt.Chart(overall_quality_summary).mark_arc().encode(
                    theta=alt.Theta(field="overall_quality_percent", type="quantitative", title='Procent'),
                    color=alt.Color(field="overall_quality", type="nominal", title='Samlet Kvalitet'),
                    tooltip=[alt.Tooltip('overall_quality:N', title='Samlet Kvalitet'), alt.Tooltip('overall_quality_percent:Q', title='Procent', format='.2f')]
                ).properties(
                    height=350,
                    width=400
                )
                st.altair_chart(quality_chart, use_container_width=True)

            with col2:
                bar_chart = alt.Chart(overall_quality_summary).mark_bar().encode(
                    x=alt.X('overall_quality:N', title='Samlet Kvalitet'),
                    y=alt.Y('Antal møder:Q', title='Antal møder'),
                    color=alt.Color('overall_quality:N', title='Samlet Kvalitet'),
                    tooltip=[alt.Tooltip('overall_quality:N', title='Samlet Kvalitet'), alt.Tooltip('Antal møder:Q', title='Antal møder')]
                ).properties(
                    height=350,
                    width=400
                )
                st.altair_chart(bar_chart, use_container_width=True)

    except Exception as e:
        st.error(f'An error occurred: {e}')
