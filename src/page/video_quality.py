import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import altair as alt
import streamlit_shadcn_ui as ui
from utils.vdx_data import get_vdx_data, get_quality_mapping, get_quality_percent, get_month_names
from utils.azure_ad_data import get_user_department


def get_video_calls_quality():
    col_1 = st.columns([1])[0]

    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Kvalitet', tag='Kvalitet', icon='bi bi-patch-check'),
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

        user_departments = get_user_department()
        if not user_departments:
            st.warning("Ingen afdelinger fundet.")
            return

        for user in user_departments:
            user['mail'] = user['mail'].lower()

        vdx_data['meeting_organized_by_name'] = vdx_data['meeting_organized_by_name'].str.lower()

        valid_departments = set(
            user['officeLocation'] for user in user_departments
            if user['mail'] in vdx_data['meeting_organized_by_name'].values
        )
        department_options = ["Alle afdelinger"] + list(valid_departments)

        selected_department = st.selectbox("Vælg en afdeling", department_options, help="Vælg en afdeling for at filtrere data.")

        selected_employee = None
        if selected_department != "Alle afdelinger":
            department_users = [user['mail'] for user in user_departments if user['officeLocation'] == selected_department]
            filtered_data = vdx_data[vdx_data['meeting_organized_by_name'].isin(department_users)]

            employee_options = ["Alle medarbejdere"] + list(set(filtered_data['meeting_organized_by_name']))
            selected_employee = st.selectbox("Vælg en medarbejder", employee_options, help="Vælg en medarbejder for at filtrere data.")

            if selected_employee != "Alle medarbejdere":
                vdx_data = filtered_data[filtered_data['meeting_organized_by_name'] == selected_employee]
            else:
                vdx_data = filtered_data

        month_names = get_month_names()

        unique_years = sorted(vdx_data['Year'].unique(), reverse=True)

        today = pd.Timestamp.today()
        default_year = today.year if today.year in unique_years else unique_years[0]
        filtered_result_year = vdx_data[vdx_data['Year'] == default_year]
        unique_months = filtered_result_year['Month'].sort_values().unique()
        default_month = today.month if today.month in unique_months else (unique_months[-1] if len(unique_months) > 0 else None)

        if (
            'last_selected_department' not in st.session_state or
            st.session_state['last_selected_department'] != selected_department or
            ('last_selected_employee' in st.session_state and st.session_state.get('last_selected_employee') != selected_employee)
        ):
            st.session_state['selected_year'] = default_year
            st.session_state['selected_month'] = default_month
            st.session_state['last_selected_department'] = selected_department
            st.session_state['last_selected_employee'] = selected_employee

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "Vælg et år",
                unique_years,
                format_func=lambda x: f'{x}',
                key='year_select',
                index=unique_years.index(st.session_state['selected_year']) if st.session_state['selected_year'] in unique_years else 0,
                help="Vælg det år, for hvilket du vil se dataene."
            )
            st.session_state['selected_year'] = selected_year

        with col2:
            filtered_result_year = vdx_data[vdx_data['Year'] == selected_year]
            unique_months = filtered_result_year['Month'].sort_values().unique()
            if (
                'selected_month' not in st.session_state
                or st.session_state['selected_year'] != selected_year
                or st.session_state['selected_month'] not in unique_months
            ):
                if today.month in unique_months:
                    st.session_state['selected_month'] = today.month
                else:
                    st.session_state['selected_month'] = unique_months[-1] if len(unique_months) > 0 else None

            selected_month = st.selectbox(
                'Vælg en måned',
                unique_months,
                format_func=lambda x: month_names[x],
                key='month_select',
                index=list(unique_months).index(st.session_state['selected_month']) if st.session_state['selected_month'] in unique_months else 0,
                help="Vælg den måned, for hvilken du vil se dataene."
            )
            st.session_state['selected_month'] = selected_month

        filtered_data = filtered_result_year[filtered_result_year['Month'] == selected_month]

        filtered_data['overall_quality'] = filtered_data['overall_quality'].map(get_quality_mapping())

        if content_tabs == 'Kvalitet':
            overall_quality_summary = filtered_data.groupby('overall_quality').size().reset_index(name='Antal møder')
            overall_quality_summary['overall_quality_percent'] = (overall_quality_summary['Antal møder'] / overall_quality_summary['Antal møder'].sum()) * 100

            col1, col2, col3 = st.columns(3)

            with col1:
                ui.metric_card(title="Høj Kvalitet", content=f"{get_quality_percent(overall_quality_summary, 'God'):.2f}%", description="Procent af møder med høj kvalitet.")
            with col2:
                ui.metric_card(title="Middel Kvalitet", content=f"{get_quality_percent(overall_quality_summary, 'Ok'):.2f}%", description="Procent af møder med middel kvalitet.")
            with col3:
                ui.metric_card(title="Ukendt Kvalitet", content=f"{get_quality_percent(overall_quality_summary, 'Ukendt'):.2f}%", description="Procent af møder med ukendt kvalitet.")

            st.write(f"### Samlet Kvalitet af VDX Møder for {month_names[selected_month]} {selected_year}")

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
