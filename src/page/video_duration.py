import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import altair as alt
from utils.vdx_data import get_vdx_data, retrieve_weekday_names, format_duration
import streamlit_shadcn_ui as ui

weekday = retrieve_weekday_names()


def get_video_calls_duration():
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

        unique_years = sorted(vdx_data['Year'].unique(), reverse=True)

        if content_tabs == 'Dag':
            unique_dates = vdx_data['start_time'].dt.date.unique()
            selected_date = st.date_input("Vælg en dato", min_value=min(unique_dates), max_value=max(unique_dates), key='date_input', help="Vælg en dato, for hvilken du vil se dataene.")

            daily_data = vdx_data[vdx_data['start_time'].dt.date == selected_date]

            avg_duration_day = daily_data['duration'].mean()
            col1, col2 = st.columns([1, 2])
            with col1:
                if pd.isna(avg_duration_day):
                    avg_duration_day_display = "Ingen data"
                else:
                    avg_duration_day_display = format_duration(int(avg_duration_day))
                ui.metric_card(title="Gennemsnitlig varighed (Dag)", content=avg_duration_day_display, description="Gennemsnitlig varighed af møder på den valgte dato.")

            if not daily_data.empty:
                daily_data['TimeInterval'] = daily_data['start_time'].dt.floor('30T')
                interval_data = daily_data.groupby('TimeInterval')['duration'].mean().reset_index(name='Gennemsnitlig varighed')

                st.write(f"## Gennemsnitlig varighed af Møder (Dag) - {selected_date}")
                day_chart = alt.Chart(interval_data).mark_bar().encode(
                    x=alt.X('TimeInterval:T', title='Tidspunkt', axis=alt.Axis(format='%H:%M')),
                    y=alt.Y('Gennemsnitlig varighed:Q', title='Gennemsnitlig varighed (minutter)', scale=alt.Scale(domain=[0, interval_data['Gennemsnitlig varighed'].max() / 60])),
                    tooltip=[alt.Tooltip('TimeInterval:T', title='Tidspunkt', format='%H:%M'), alt.Tooltip('Gennemsnitlig varighed:Q', title='Gennemsnitlig varighed', format='.2f')]
                ).transform_calculate(
                    "Gennemsnitlig varighed", "datum['Gennemsnitlig varighed'] / 60"
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

            week_data = filtered_result_year[filtered_result_year['Week'] == selected_week]

            avg_duration_week = week_data['duration'].mean()
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Gennemsnitlig varighed (Uge)", content=format_duration(int(avg_duration_week)), description="Gennemsnitlig varighed af møder i den valgte uge.")

            week_data_grouped = week_data.groupby(['Week', 'Weekday'])['duration'].mean().reset_index(name='Gennemsnitlig varighed')

            st.write(f"## Gennemsnitlig varighed af Møder (Uge) - {selected_year_week}, Uge {selected_week}")
            week_chart = alt.Chart(week_data_grouped).mark_bar().encode(
                x=alt.X('Weekday', title='Ugedag', sort=['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lørdag', 'Søndag']),
                y=alt.Y('Gennemsnitlig varighed:Q', title='Gennemsnitlig varighed (minutter)', scale=alt.Scale(domain=[0, week_data_grouped['Gennemsnitlig varighed'].max() / 60])),
                tooltip=[alt.Tooltip('Weekday', title='Ugedag'), alt.Tooltip('Gennemsnitlig varighed:Q', title='Gennemsnitlig varighed', format='.2f')]
            ).transform_calculate(
                "Gennemsnitlig varighed", "datum['Gennemsnitlig varighed'] / 60"
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

            month_data = filtered_result_year[filtered_result_year['Month'] == selected_month]

            avg_duration_month = month_data['duration'].mean()
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Gennemsnitlig varighed (Måned)", content=format_duration(int(avg_duration_month)), description="Gennemsnitlig varighed af møder i den valgte måned.")

            month_data_grouped = month_data.groupby(['Month', 'Månedsdag'])['duration'].mean().reset_index(name='Gennemsnitlig varighed')

            st.write(f"## Gennemsnitlig varighed af Møder (Måned) - {selected_year_month}, Måned {month_names[selected_month]}")
            month_chart = alt.Chart(month_data_grouped).mark_bar().encode(
                x=alt.X('Månedsdag:O', title='Månedsdag', axis=alt.Axis(format='d')),
                y=alt.Y('Gennemsnitlig varighed:Q', title='Gennemsnitlig varighed (minutter)', scale=alt.Scale(domain=[0, month_data_grouped['Gennemsnitlig varighed'].max() / 60])),
                tooltip=[alt.Tooltip('Månedsdag:O', title='Månedsdag'), alt.Tooltip('Gennemsnitlig varighed:Q', title='Gennemsnitlig varighed', format='.2f')]
            ).transform_calculate(
                "Gennemsnitlig varighed", "datum['Gennemsnitlig varighed'] / 60"
            ).properties(
                width=600,
                height=400
            )

            st.altair_chart(month_chart, use_container_width=True)

    except Exception as e:
        st.error(f'An error occurred: {e}')
