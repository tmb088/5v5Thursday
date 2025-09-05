import streamlit as st
import pandas as pd
from collections import defaultdict
import random
import os

# Set page configuration
st.set_page_config(
    page_title="5v5 Team Generator",
    page_icon="⚽",
    layout="wide"
)

# App title
st.title("⚽ 5v5 Team Generator")
st.markdown("Automatically loads data from 'thursday_football.xlsx' in the same directory.")

# Initialize session state
if 'player_data' not in st.session_state:
    st.session_state.player_data = {}
if 'performance' not in st.session_state:
    st.session_state.performance = defaultdict(lambda: {'score': 0, 'games': 0})
if 'synergy' not in st.session_state:
    st.session_state.synergy = defaultdict(lambda: defaultdict(int))
if 'selected_players' not in st.session_state:
    st.session_state.selected_players = []

# File name to read
DATA_FILE = "thursday_football.xlsx"

def get_team_from_value(cell_value):
    """
    Determine team from cell value
    """
    if pd.isna(cell_value) or cell_value is None:
        return 'none', None
    
    cell_value = str(cell_value).strip().upper()
    
    # Check if value contains team prefix
    if cell_value.startswith('R:'):
        return 'red', cell_value[2:]
    elif cell_value.startswith('W:'):
        return 'white', cell_value[2:]
    elif cell_value.startswith('B:'):
        return 'none', cell_value[2:]
    else:
        # If no prefix, assume white team
        return 'white', cell_value

def load_player_data():
    """Load player data from the fixed file name"""
    try:
        # Check if file exists
        if not os.path.exists(DATA_FILE):
            st.error(f"Data file '{DATA_FILE}' not found. Please make sure it's in the same directory as this app.")
            return {}
        
        # Read the Excel file
        df = pd.read_excel(DATA_FILE)
        
        player_data = {}
        for idx, row in df.iterrows():
            player = row.iloc[0]
            if pd.isna(player) or not player:
                continue
                
            player = str(player).strip()
            player_data[player] = []
            
            for cell in row[1:]:
                if pd.isna(cell) or not cell:
                    player_data[player].append(('none', None))
                    continue
                    
                team, result = get_team_from_value(cell)
                player_data[player].append((team, result))
                
        return player_data
    except Exception as e:
        st.error(f"Error loading data from {DATA_FILE}: {str(e)}")
        return {}

def analyze_stats(player_data):
    """Analyze player performance and synergy statistics"""
    performance = defaultdict(lambda: {'score': 0, 'games': 0})
    synergy = defaultdict(lambda: defaultdict(int))

    if not player_data:
        return performance, synergy
        
    # Find maximum number of games
    num_days = max(len(games) for games in player_data.values()) if player_data else 0
    
    for day_index in range(num_days):
        red_team = []

        for player, games in player_data.items():
            if day_index >= len(games):
                continue
                
            team, result = games[day_index]

            if result in ['W', 'D', 'L']:
                performance[player]['games'] += 1
                score = {'W': 1, 'D': 0, 'L': -1}[result]
                performance[player]['score'] += score

                if team == 'red':
                    red_team.append(player)

        # Update synergy counts for players who played together on red team
        for i, p1 in enumerate(red_team):
            for p2 in red_team[i+1:]:
                synergy[p1][p2] += 1
                synergy[p2][p1] += 1
                
    return performance, synergy

def generate_teams(players, performance, synergy):
    """Generate balanced teams based on performance and synergy"""
    if not players:
        return [], []
        
    # Sort players by performance
    sorted_players = sorted(players, key=lambda p: performance[p]['score'] / max(1, performance[p]['games']), reverse=True)
    team1, team2 = [], []

    for player in sorted_players:
        team1_synergy = sum(synergy[player][p] for p in team1)
        team2_synergy = sum(synergy[player][p] for p in team2)

        if len(team1) < len(team2):
            team1.append(player)
        elif len(team2) < len(team1):
            team2.append(player)
        else:
            if team1_synergy < team2_synergy:
                team1.append(player)
            else:
                team2.append(player)
                
    return team1, team2

# Load data automatically when the app starts
if not st.session_state.player_data:
    with st.spinner("Loading data from file..."):
        st.session_state.player_data = load_player_data()
        if st.session_state.player_data:
            st.session_state.performance, st.session_state.synergy = analyze_stats(st.session_state.player_data)

# Display app content based on whether data was loaded
if st.session_state.player_data:
    st.success(f"Data loaded successfully from '{DATA_FILE}'! Found {len(st.session_state.player_data)} players.")
    
    # Player selection
    st.subheader("Select Players")
    all_players = sorted(st.session_state.player_data.keys())
    
    # Create two columns for player selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Available Players**")
        for player in all_players:
            if player not in st.session_state.selected_players:
                if st.button(f"➕ {player}", key=f"add_{player}"):
                    if len(st.session_state.selected_players) < 10:
                        st.session_state.selected_players.append(player)
                    else:
                        st.warning("Maximum of 10 players already selected")
    
    with col2:
        st.markdown("**Selected Players**")
        for player in st.session_state.selected_players:
            if st.button(f"➖ {player}", key=f"remove_{player}"):
                st.session_state.selected_players.remove(player)
    
    st.info(f"{len(st.session_state.selected_players)} of 10 players selected")
    
    # Display player stats
    with st.expander("View Player Statistics"):
        stats_data = []
        for player in all_players:
            perf = st.session_state.performance[player]
            win_rate = (perf['score'] + perf['games']) / (2 * perf['games']) if perf['games'] > 0 else 0
            stats_data.append({
                'Player': player,
                'Score': perf['score'],
                'Games': perf['games'],
                'Win Rate': f"{win_rate:.2%}"
            })
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Random Select", help="Randomly select 10 players"):
            if len(all_players) >= 10:
                st.session_state.selected_players = random.sample(all_players, 10)
            else:
                st.error("Not enough players in the dataset")
    
    with col2:
        if st.button("🧹 Clear All", help="Clear all selections"):
            st.session_state.selected_players = []
            
    with col3:
        if st.button("📊 Generate Teams", disabled=len(st.session_state.selected_players) != 10,
                    help="Generate balanced teams from selected players"):
            team1, team2 = generate_teams(
                st.session_state.selected_players, 
                st.session_state.performance, 
                st.session_state.synergy
            )
            
            # Display results
            st.subheader("Team Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏆 Team Red")
                team1_score = 0
                team1_games = 0
                for player in team1:
                    perf = st.session_state.performance[player]
                    team1_score += perf['score']
                    team1_games += perf['games']
                    win_rate = (perf['score'] + perf['games']) / (2 * perf['games']) if perf['games'] > 0 else 0
                    st.write(f"**{player}** (Score: {perf['score']}, Games: {perf['games']}, Win Rate: {win_rate:.2%})")
                
                st.metric("Team Red Total", f"Score: {team1_score} | Games: {team1_games}")
            
            with col2:
                st.markdown("### ⚪ Team White")
                team2_score = 0
                team2_games = 0
                for player in team2:
                    perf = st.session_state.performance[player]
                    team2_score += perf['score']
                    team2_games += perf['games']
                    win_rate = (perf['score'] + perf['games']) / (2 * perf['games']) if perf['games'] > 0 else 0
                    st.write(f"**{player}** (Score: {perf['score']}, Games: {perf['games']}, Win Rate: {win_rate:.2%})")
                
                st.metric("Team White Total", f"Score: {team2_score} | Games: {team2_games}")
            
            # Calculate team balance
            balance_score = abs(team1_score - team2_score)
            st.metric("Team Balance Score", f"{balance_score}", 
                     delta="Well balanced" if balance_score <= 2 else "Some imbalance")

else:
    st.error(f"Could not load data from '{DATA_FILE}'. Please make sure the file exists in the same directory as this app.")

# Add instructions
with st.expander("📋 File Format Instructions"):
    st.markdown("""
    Your Excel file should follow this format:
    - **First column**: Player names
    - **Subsequent columns**: Match results using these codes:
    
    ### Team Codes (prefix):
    - 🔴 **Red Team**: Prefix with `R:` (e.g., `R:W`)
    - ⚪ **White Team**: Prefix with `W:` or no prefix (e.g., `W:L` or just `L`)
    - ⚫ **Did Not Play**: Prefix with `B:` (e.g., `B:W`)
    
    ### Result Codes:
    - ✅ **Win**: `W`
    - 🔄 **Draw**: `D`
    - ❌ **Loss**: `L`
    
    ### Example row:
    | Player Name | Match 1 | Match 2 | Match 3 |
    |-------------|---------|---------|---------|
    | John Doe    | R:W     | W:L     | B:W     |
    """)

# Add footer
st.markdown("---")
st.markdown("### Need help?")
st.markdown(f"1. Make sure '{DATA_FILE}' exists in the same directory as this app")
st.markdown("2. Check that your Excel file follows the format above")
st.markdown("3. The app will automatically load data when it starts")