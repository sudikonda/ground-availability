from bs4 import BeautifulSoup
from datetime import datetime

# Load the HTML file with all grounds
with open('all-grounds.html', 'r', encoding='utf-8') as file:
    all_grounds_content = file.read()

# Parse the HTML for grounds
soup_grounds = BeautifulSoup(all_grounds_content, 'html.parser')

# Extract all ground names from the 'Grounds' section
all_grounds = []
ground_panels = soup_grounds.find_all('div', class_='panel-body')
for panel in ground_panels:
    ground_name_elements = panel.find_all('span')
    for ground_name_element in ground_name_elements:
        ground_name = ground_name_element.get_text(strip=True)
        if ground_name and 'Park' in ground_name:  # Filter to avoid irrelevant data
            all_grounds.append(ground_name)

# Load the match HTML file
with open('sample-response.html', 'r', encoding='utf-8') as file:
    content = file.read()

# Parse the HTML for match data
soup = BeautifulSoup(content, 'html.parser')

# Get today's date and time
today = datetime.today().strftime('%b %d')  # Example: 'Oct 05'
current_time = datetime.now()

# Initialize list to store ground availability and match information
grounds_in_use_today = []
matches_today = []

# Find all the relevant ground information from the match schedule
matches = soup.find_all('div', {'matchno': True})

# Initialize a list to store match details
match_details = []

# Iterate through the matches and extract relevant details
for match in matches:
    match_no = match.get('matchno')  # Extract match number
    home_team_id = match.get('htid')  # Extract home team ID
    visiting_team_id = match.get('vtid')  # Extract visiting team ID
    umpire_team_id = match.get('utid')  # Extract umpire team ID

    # Extract additional information (like teams and ground) if needed
    teams = match.find_all('a', class_='text-dark')
    ground = match.find('a', title="Ground Directions")
    date_time = match.find_all('div', class_='text-nowrap')

    home_team_name = teams[0].get_text(strip=True) if teams else "N/A"
    visiting_team_name = teams[1].get_text(strip=True) if teams else "N/A"
    ground_name = ground.get_text(strip=True) if ground else "N/A"
    match_time = date_time[0].get_text(strip=True) if date_time else "N/A"
    match_date = date_time[1].get_text(strip=True) if date_time else "N/A"

    # Check if the match is today
    if today in match_date:
        # Append to the list of matches today
        matches_today.append({
            'match_no': match_no,
            'home_team_id': home_team_id,
            'visiting_team_id': visiting_team_id,
            'umpire_team_id': umpire_team_id,
            'home_team_name': home_team_name,
            'visiting_team_name': visiting_team_name,
            'ground_name': ground_name,
            'match_time': match_time,
            'match_date': match_date
        })

        # Add ground to the list of grounds in use today
        grounds_in_use_today.append(ground_name)

    # Append the match data to the list
    match_details.append({
        'match_no': match_no,
        'home_team_id': home_team_id,
        'visiting_team_id': visiting_team_id,
        'umpire_team_id': umpire_team_id,
        'home_team_name': home_team_name,
        'visiting_team_name': visiting_team_name,
        'ground_name': ground_name,
        'match_time': match_time,
        'match_date': match_date
    })

# # Identify available grounds by removing the ones in use
available_grounds = [ground for ground in all_grounds if ground not in grounds_in_use_today]

# Group matches by ground
matches_by_ground = {}
for match in matches_today:
    if match['ground_name'] not in matches_by_ground:
        matches_by_ground[match['ground_name']] = []
    matches_by_ground[match['ground_name']].append(match)

# Display matches by ground
for ground, matches in matches_by_ground.items():
    print(f"Matches scheduled for today on Ground: {ground}\n")
    for match in matches:
        print(f"Home Team: {match['home_team_name']}, Visiting Team: {match['visiting_team_name']}")
        print(f"Ground: {match['ground_name']}, Date: {match['match_date']}, Time: {match['match_time']}\n")


# Display available grounds today
print("\n No Games Scheduled for Today. Available grounds today:")
for ground in available_grounds:
    print(f"Ground: {ground}")
