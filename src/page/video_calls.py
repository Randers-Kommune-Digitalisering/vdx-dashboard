import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import altair as alt
from utils.vdx_data import get_vdx_data, retrieve_weekday_names
import streamlit_shadcn_ui as ui
from utils.azure_ad_data import get_user_department

weekday = retrieve_weekday_names()


def get_video_calls():
    col_1 = st.columns([1])[0]

    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Dag', tag='Dag'),
            sac.TabsItem('Uge', tag='Uge'),
            sac.TabsItem('Måned', tag='Måned'),
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

        if content_tabs == 'Dag':
            unique_dates = vdx_data['start_time'].dt.date.unique()
            min_date, max_date = min(unique_dates), max(unique_dates)

            if 'date_input' in st.session_state and st.session_state['date_input'] not in unique_dates:
                st.session_state['date_input'] = min_date

            selected_date = st.date_input(
                "Vælg en dato",
                value=st.session_state.get('date_input', min_date),
                min_value=min_date,
                max_value=max_date,
                key='date_input',
                help="Vælg en dato, for hvilken du vil se dataene."
            )

            daily_data = vdx_data[vdx_data['start_time'].dt.date == selected_date]

            total_calls_day = daily_data.shape[0]
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(
                    title="Samlet antal møder (Dag)",
                    content=total_calls_day,
                    description=f"Antal møder, der blev afholdt den {selected_date}."
                )

            daily_data['TimeInterval'] = daily_data['start_time'].dt.floor('30T')
            interval_data = daily_data.groupby('TimeInterval').size().reset_index(name='Antal møder')

            st.write(f"## Antal af Møder (Dag) - {selected_date}")
            day_chart = alt.Chart(interval_data).mark_bar().encode(
                x=alt.X('TimeInterval:T', title='Tidspunkt', axis=alt.Axis(format='%H:%M')),
                y=alt.Y('Antal møder:Q', title='Antal møder'),
                tooltip=[
                    alt.Tooltip('TimeInterval:T', title='Tidspunkt', format='%H:%M'),
                    alt.Tooltip('Antal møder:Q', title='Antal møder')
                ]
            ).properties(
                height=700,
                width=900
            )

            st.altair_chart(day_chart, use_container_width=True)

        elif content_tabs == 'Uge':
            vdx_data['Week'] = vdx_data['start_time'].dt.isocalendar().week
            vdx_data['Weekday'] = vdx_data['start_time'].dt.day_name().map(weekday)

            col1, col2 = st.columns(2)
            with col1:
                selected_year_week = st.selectbox(
                    "Vælg et år",
                    unique_years,
                    format_func=lambda x: f'{x}',
                    index=unique_years.tolist().index(st.session_state['selected_year_week']) if 'selected_year_week' in st.session_state and st.session_state['selected_year_week'] is not None else 0,
                    key='year_select_week',
                    help="Vælg det år, for hvilket du vil se dataene."
                )
            with col2:
                filtered_result_year = vdx_data[vdx_data['Year'] == selected_year_week]
                unique_weeks = filtered_result_year['Week'].sort_values().unique()
                selected_week = st.selectbox('Vælg en uge', unique_weeks, help="Vælg den uge, for hvilken du vil se dataene.")

            week_data = filtered_result_year[filtered_result_year['Week'] == selected_week].groupby(['Week', 'Weekday']).size().reset_index(name='Antal møder')

            total_calls_week = week_data['Antal møder'].sum()
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Samlet antal møder (Uge)", content=int(total_calls_week), description=f"Antal møder, der blev afholdt i Uge {selected_week}.")

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

            col1, col2 = st.columns(2)
            with col1:
                selected_year_month = st.selectbox(
                    "Vælg et år",
                    unique_years,
                    format_func=lambda x: f'{x}',
                    index=unique_years.tolist().index(st.session_state['selected_year_month']) if 'selected_year_month' in st.session_state and st.session_state['selected_year_month'] is not None else 0,
                    key='year_select_month',
                    help="Vælg det år, for hvilket du vil se dataene."
                )
            with col2:
                filtered_result_year = vdx_data[vdx_data['Year'] == selected_year_month]
                unique_months = filtered_result_year['Month'].sort_values().unique()
                selected_month = st.selectbox('Vælg en måned', unique_months, format_func=lambda x: month_names[x], help="Vælg den måned, for hvilken du vil se dataene.")

            month_data = filtered_result_year[filtered_result_year['Month'] == selected_month].groupby(['Month', 'Månedsdag']).size().reset_index(name='Antal møder')

            total_calls_month = month_data['Antal møder'].sum()
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Samlet antal møder (Måned)", content=int(total_calls_month), description=f"Antal møder, der blev afholdt i {month_names[selected_month]}.")

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
