import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


@st.cache_data
def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return BeautifulSoup(content, 'html.parser')
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def extract_ground_names(soup):
    all_grounds = []
    ground_panels = soup.find_all('div', class_='panel-body')
    for panel in ground_panels:
        ground_name_elements = panel.find_all('span')
        for ground_name_element in ground_name_elements:
            ground_name = ground_name_element.get_text(strip=True)
            if ground_name and 'Park' in ground_name:
                all_grounds.append(ground_name)
    return all_grounds


def extract_match_info(match):
    match_no = match.get('matchno')
    home_team_id = match.get('htid')
    visiting_team_id = match.get('vtid')
    umpire_team_id = match.get('utid')
    teams = match.find_all('a', class_='text-dark')
    ground = match.find('a', title="Ground Directions")
    date_time = match.find_all('div', class_='text-nowrap')

    return {
        'match_no': match_no,
        'home_team_id': home_team_id,
        'visiting_team_id': visiting_team_id,
        'umpire_team_id': umpire_team_id,
        'home_team_name': teams[0].get_text(strip=True) if teams else "N/A",
        'visiting_team_name': teams[1].get_text(strip=True) if teams else "N/A",
        'ground_name': ground.get_text(strip=True) if ground else "N/A",
        'match_time': date_time[0].get_text(strip=True) if date_time else "N/A",
        'match_date': date_time[1].get_text(strip=True) if date_time else "N/A"
    }


def process_match_data(soup, selected_date):
    matches_today = []
    grounds_in_use_today = set()
    matches = soup.find_all('div', {'matchno': True})

    for match in matches:
        match_info = extract_match_info(match)
        if selected_date in match_info['match_date']:
            matches_today.append(match_info)
            grounds_in_use_today.add(match_info['ground_name'])

    return matches_today, grounds_in_use_today


def main():
    # Show the page title and description.
    st.set_page_config(page_title="Ground Availability and Matches Schedule - Streamlit App", page_icon="🏏")
    st.title("🏃🏼‍♂️‍➡ Ground Availability and Matches Schedule 🏏️")

    selected_date = st.date_input("Select a date", datetime.today())
    date_str = selected_date.strftime('%b %d')

    grounds_soup = load_data('data/all-grounds.html')
    matches_soup = load_data('data/sample-response.html')

    if grounds_soup is None or matches_soup is None:
        return

    all_grounds = extract_ground_names(grounds_soup)
    matches_today, grounds_in_use_today = process_match_data(matches_soup, date_str)

    available_grounds = [ground for ground in all_grounds if ground not in grounds_in_use_today]

    matches_by_ground = {}
    for match in matches_today:
        if match['ground_name'] not in matches_by_ground:
            matches_by_ground[match['ground_name']] = []
        matches_by_ground[match['ground_name']].append(match)

    st.subheader(f"Matches scheduled for {date_str} by Ground:")
    if matches_by_ground:
        for ground, matches in matches_by_ground.items():
            with st.expander(f"Ground: {ground}"):
                match_data = []
                for match in matches:
                    match_data.append({
                        "Home Team": match['home_team_name'],
                        "Visiting Team": match['visiting_team_name'],
                        "Match Time": match['match_time'],
                        "Date": match['match_date']
                    })
                df = pd.DataFrame(match_data)
                st.table(df)
    else:
        st.write(f"No matches scheduled for {date_str}.")

    # Display available grounds today
    st.subheader(f"Available Grounds for {date_str}:")
    if available_grounds:
        with st.expander("Click to view available grounds"):
            df_available = pd.DataFrame({"Available Grounds": available_grounds})
            st.table(df_available)
    else:
        st.write("No available grounds for the selected date.")


if __name__ == "__main__":
    main()