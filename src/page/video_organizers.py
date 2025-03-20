import streamlit as st
import streamlit_antd_components as sac
import pandas as pd
import altair as alt
from utils.vdx_data import get_vdx_data, extract_organizers_from_email
import streamlit_shadcn_ui as ui


def get_video_calls_organizers():
    col_1 = st.columns([1])[0]

    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Organisator', tag='Organisator'),
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
        vdx_data['organizer_name'] = vdx_data['meeting_organized_by_name'].apply(extract_organizers_from_email)

        if content_tabs == 'Organisator':
            unique_organizers = vdx_data['organizer_name'].unique()
            selected_organizer = st.selectbox('Vælg en organisator', unique_organizers, help="Vælg den organisator, for hvilken du vil se dataene.")

            organizer_data = vdx_data[vdx_data['organizer_name'] == selected_organizer]

            total_calls_organizer = organizer_data.shape[0]
            col1, col2 = st.columns([1, 2])
            with col1:
                ui.metric_card(title="Samlet antal møder (Organisator)", content=total_calls_organizer, description=f"Antal møder, der blev organiseret af {selected_organizer}.")

            organizer_data['Date'] = organizer_data['start_time'].dt.date
            organizer_summary = organizer_data.groupby('Date').size().reset_index(name='Antal møder')

            st.write(f"## Antal af Møder (Organisator) - {selected_organizer}")
            organizer_chart = alt.Chart(organizer_summary).mark_bar().encode(
                x=alt.X('Date:T', title='Dato', axis=alt.Axis(format='%Y-%m-%d')),
                y=alt.Y('Antal møder:Q', title='Antal møder'),
                tooltip=[alt.Tooltip('Date:T', title='Dato', format='%Y-%m-%d'), alt.Tooltip('Antal møder:Q', title='Antal møder')]
            ).properties(
                height=700,
                width=900
            )

            st.altair_chart(organizer_chart, use_container_width=True)

    except Exception as e:
        st.error(f'An error occurred: {e}')
