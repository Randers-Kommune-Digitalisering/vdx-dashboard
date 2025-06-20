import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import altair as alt
from utils.vdx_data import get_vdx_data, retrieve_weekday_names
import streamlit_shadcn_ui as ui
from utils.azure_ad_data import get_user_department
import datetime

weekday = retrieve_weekday_names()


def get_video_calls():
    col_1 = st.columns([1])[0]

    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Uge', tag='Uge', icon='calendar-week'),
            sac.TabsItem('Måned', tag='Måned', icon='calendar-month'),
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

        if selected_department != "Alle afdelinger":
            department_users = [user['mail'] for user in user_departments if user['officeLocation'] == selected_department]
            filtered_data = vdx_data[vdx_data['meeting_organized_by_name'].isin(department_users)]

            employee_options = ["Alle medarbejdere"] + list(set(filtered_data['meeting_organized_by_name']))
            selected_employee = st.selectbox("Vælg en medarbejder", employee_options, help="Vælg en medarbejder for at filtrere data.")

            if selected_employee != "Alle medarbejdere":
                vdx_data = filtered_data[filtered_data['meeting_organized_by_name'] == selected_employee]
            else:
                vdx_data = filtered_data

        unique_years = sorted(vdx_data['Year'].unique(), reverse=True)

        if content_tabs == 'Uge':
            vdx_data['Week'] = vdx_data['start_time'].dt.isocalendar().week
            vdx_data['Weekday'] = vdx_data['start_time'].dt.day_name().map(weekday)

            today = datetime.date.today()
            current_year, current_week, _ = today.isocalendar()
            default_year = current_year if current_year in unique_years else unique_years[0]
            filtered_result_year = vdx_data[vdx_data['Year'] == default_year]
            unique_weeks = filtered_result_year['Week'].sort_values().unique()
            default_week = current_week if current_week in unique_weeks else unique_weeks[-1]

            col1, col2 = st.columns(2)
            with col1:
                if 'selected_year_week' not in st.session_state:
                    st.session_state['selected_year_week'] = default_year

                selected_year_week = st.selectbox(
                    "Vælg et år",
                    unique_years,
                    key='selected_year_week',
                    format_func=lambda x: f'{x}',
                    help="Vælg det år, for hvilket du vil se dataene."
                )

            with col2:
                filtered_result_year = vdx_data[vdx_data['Year'] == selected_year_week]
                unique_weeks = filtered_result_year['Week'].sort_values().unique()

                if (
                    'selected_week' not in st.session_state or
                    st.session_state['selected_year_week'] != selected_year_week or
                    st.session_state['selected_week'] not in unique_weeks
                ):
                    if default_week in unique_weeks:
                        st.session_state['selected_week'] = default_week
                    else:
                        st.session_state['selected_week'] = unique_weeks[-1] if len(unique_weeks) > 0 else None

                selected_week = st.selectbox(
                    'Vælg en uge',
                    unique_weeks,
                    key='selected_week',
                    help="Vælg den uge, for hvilken du vil se dataene."
                )

            week_data = filtered_result_year[filtered_result_year['Week'] == selected_week].groupby(['Week', 'Weekday']).size().reset_index(name='Antal møder')

            total_calls_week = week_data['Antal møder'].sum()
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Samlet antal møder (Uge)", content=int(total_calls_week), description=f"Antal møder, der blev afholdt i Uge {selected_week} og År {selected_year_week}")

            st.write(f"## Antal af Møder (Uge) - {selected_year_week}, Uge {selected_week}")
            week_chart = alt.Chart(week_data).mark_bar().encode(
                x=alt.X('Weekday', title='Ugedag', sort=['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lørdag', 'Søndag']),
                y=alt.Y('Antal møder', title='Antal møder'),
                tooltip=[alt.Tooltip('Weekday', title='Ugedag'), 'Antal møder']
            ).properties(
                width=600,
                height=400
            )

            st.altair_chart(week_chart, use_container_width=True)

        elif content_tabs == 'Måned':
            vdx_data['Month'] = vdx_data['start_time'].dt.month
            vdx_data['Månedsdag'] = vdx_data['start_time'].dt.day.astype(int)

            month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}

            today = datetime.date.today()
            current_year = today.year
            current_month = today.month

            default_year = current_year if current_year in unique_years else unique_years[0]

            filtered_result_year = vdx_data[vdx_data['Year'] == default_year]
            unique_months = filtered_result_year['Month'].sort_values().unique()
            if len(unique_months) > 0:
                default_month = current_month if current_month in unique_months else unique_months[-1]
            else:
                default_month = None

            col1, col2 = st.columns(2)
            with col1:
                if 'selected_year_month' not in st.session_state or st.session_state['selected_year_month'] not in unique_years:
                    st.session_state['selected_year_month'] = default_year

                selected_year_month = st.selectbox(
                    "Vælg et år",
                    unique_years,
                    format_func=lambda x: f'{x}',
                    key='year_select_month',
                    help="Vælg det år, for hvilket du vil se dataene."
                )
            with col2:
                filtered_result_year = vdx_data[vdx_data['Year'] == selected_year_month]
                unique_months = filtered_result_year['Month'].sort_values().unique()

                if (
                    'selected_month' not in st.session_state or
                    st.session_state['selected_year_month'] != selected_year_month or
                    st.session_state['selected_month'] not in unique_months
                ):
                    if len(unique_months) > 0:
                        if default_month in unique_months:
                            st.session_state['selected_month'] = default_month
                        else:
                            st.session_state['selected_month'] = unique_months[-1]
                    else:
                        st.session_state['selected_month'] = None

                selected_month_tmp = st.selectbox(
                    'Vælg en måned',
                    unique_months,
                    format_func=lambda x: month_names[x],
                    key=f'select_month_{selected_year_month}',
                    index=list(unique_months).index(st.session_state['selected_month']) if st.session_state['selected_month'] in unique_months else 0,
                    help="Vælg den måned, for hvilken du vil se dataene."
                )

                if selected_month_tmp != st.session_state['selected_month']:
                    st.session_state['selected_month'] = selected_month_tmp

                selected_month = st.session_state['selected_month']

            month_data = filtered_result_year[filtered_result_year['Month'] == selected_month].groupby(['Month', 'Månedsdag']).size().reset_index(name='Antal møder')

            total_calls_month = month_data['Antal møder'].sum()
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Samlet antal møder (Måned)", content=int(total_calls_month), description=f"Antal møder, der blev afholdt i {month_names[selected_month]} og år {selected_year_month} ")

            st.write(f"## Antal af Møder (Måned) - {selected_year_month}, Måned {month_names[selected_month]}")
            month_chart = alt.Chart(month_data).mark_bar().encode(
                x=alt.X('Månedsdag:O', title='Månedsdag', axis=alt.Axis(format='d')),
                y=alt.Y('Antal møder:Q', title='Antal møder'),
                tooltip=[alt.Tooltip('Månedsdag:O', title='Månedsdag'), alt.Tooltip('Antal møder:Q', title='Antal møder')]
            ).properties(
                width=600,
                height=400
            )

            st.altair_chart(month_chart, use_container_width=True)

    except Exception as e:
        st.error(f'An error occurred: {e}')
