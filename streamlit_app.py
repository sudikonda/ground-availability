from datetime import datetime

import pandas as pd
import streamlit as st

from acl_schedule import get_acl_schedule_main
from gcl_schedule import get_gcl_schedule_main


def main():
    st.set_page_config(page_title="Ground Availability and Matches Schedule", page_icon="🏏")
    st.title("🏃🏼Ground Availability and Matches Schedule 🏏️")

    selected_date = st.date_input("Select a date", min_value=datetime.today())
    acl_date_str = selected_date.strftime('%a, %b %d')
    gcl_date_str = f"{selected_date:%A, %b} {selected_date:%Y} {selected_date.day}"

    acl_schedule_data = get_acl_schedule_main()
    gcl_schedule_data = get_gcl_schedule_main()

    if acl_schedule_data is None and gcl_schedule_data is None:
        st.error("Error fetching data. Please try again later.")
        return

    all_grounds = acl_schedule_data['all_grounds']
    matches = acl_schedule_data['matches'] + gcl_schedule_data['matches']

    matches_today = [match for match in matches if acl_date_str in match['match_date'] or gcl_date_str in match['match_date']]
    grounds_in_use_today = set(match['ground_name'] for match in matches_today)
    available_grounds = [ground for ground in all_grounds if ground not in grounds_in_use_today]

    st.subheader(f"Matches scheduled for {acl_date_str} by Ground:")
    if matches_today:
        for ground in grounds_in_use_today:
            with st.expander(ground):
                ground_matches = [match for match in matches_today if match['ground_name'] == ground]
                df = pd.DataFrame(ground_matches)
                st.table(df[['league','home_team_name', 'visiting_team_name', 'match_time', 'match_date']])
    else:
        st.write(f"No matches scheduled for {acl_date_str}.")

    st.subheader(f"Available Grounds for {acl_date_str}:")
    if available_grounds:
        with st.expander("Click to view available grounds"):
            df_available = pd.DataFrame({"Available Grounds": available_grounds})
            st.table(df_available)
    else:
        st.write("No available grounds for the selected date.")


if __name__ == "__main__":
    main()