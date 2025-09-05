import streamlit as st
import pandas as pd
from collections import defaultdict
import random
import os
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="5v5 Team Generator",
    page_icon="⚽",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1f77b4;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.3rem;
        margin-top: 1.5rem;
    }
    .team-section {
        background-color: #f0f8ff;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #3498db;
    }
    .team-red {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #000000 !important;
    }
    .team-white {
        background-color: #f5f5f5;
        border-left: 4px solid #9e9e9e;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #000000 !important;
    }
    .player-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3498db;
        color: #000000 !important;
    }
    .stButton button {
        width: 100%;
    }
    .team-header {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #2c3e50 !important;
    }
    .balance-good {
        color: green;
        font-weight: bold;
    }
    .balance-fair {
        color: orange;
        font-weight: bold;
    }
    .balance-poor {
        color: red;
        font-weight: bold;
    }
    /* Ensure all text is visible */
    .stMarkdown, .stInfo, .stSuccess, .stWarning, .stError {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown('<h1 class="main-header">⚽ 5v5 Team Generator</h1>', unsafe_allow_html=True)
st.markdown("Automatically loads data from 'thursday_football.xlsx' in the same directory.")

# Initialize session state
if 'player_data' not in st.session_state:
    st.session_state.player_data = {}
if 'performance' not in st.session_state:
    st.session_state.performance = defaultdict(lambda: {'score': 0, 'games': 0, 'wins': 0, 'losses': 0, 'draws': 0})
if 'synergy' not in st.session_state:
    st.session_state.synergy = defaultdict(lambda: defaultdict(int))
if 'selected_players' not in st.session_state:
    st.session_state.selected_players = []
if 'teams_generated' not in st.session_state:
    st.session_state.teams_generated = False
if 'team1' not in st.session_state:
    st.session_state.team1 = []
if 'team2' not in st.session_state:
    st.session_state.team2 = []
if 'last_teams' not in st.session_state:
    st.session_state.last_teams = {}
if 'team_history' not in st.session_state:
    st.session_state.team_history = []

# File name to read
DATA_FILE = "thursday_football.xlsx"

def get_team_from_value(cell_value):
    """Determine team from cell value"""
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
    performance = defaultdict(lambda: {'score': 0, 'games': 0, 'wins': 0, 'losses': 0, 'draws': 0})
    synergy = defaultdict(lambda: defaultdict(int))

    if not player_data:
        return performance, synergy
        
    # Find maximum number of games
    num_days = max(len(games) for games in player_data.values()) if player_data else 0
    
    for day_index in range(num_days):
        red_team = []
        white_team = []

        for player, games in player_data.items():
            if day_index >= len(games):
                continue
                
            team, result = games[day_index]

            if result in ['W', 'D', 'L']:
                performance[player]['games'] += 1
                score = {'W': 1, 'D': 0, 'L': -1}[result]
                performance[player]['score'] += score
                
                # Track wins, losses, draws
                if result == 'W':
                    performance[player]['wins'] += 1
                elif result == 'L':
                    performance[player]['losses'] += 1
                else:
                    performance[player]['draws'] += 1

                if team == 'red':
                    red_team.append(player)
                elif team == 'white':
                    white_team.append(player)

        # Update synergy counts for players who played together on the same team
        for i, p1 in enumerate(red_team):
            for p2 in red_team[i+1:]:
                synergy[p1][p2] += 1
                synergy[p2][p1] += 1
                
        for i, p1 in enumerate(white_team):
            for p2 in white_team[i+1:]:
                synergy[p1][p2] += 1
                synergy[p2][p1] += 1
                
    return performance, synergy

def calculate_player_rating(performance, player):
    """Calculate a player rating based on performance"""
    if performance[player]['games'] == 0:
        return 0
    
    win_rate = performance[player]['wins'] / performance[player]['games']
    score_per_game = performance[player]['score'] / performance[player]['games']
    
    # Weight recent performance more heavily (simple version)
    return (win_rate * 0.7 + score_per_game * 0.3) * 10

def generate_teams(players, performance, synergy):
    """Generate balanced teams based on performance and synergy"""
    if not players or len(players) != 10:
        return [], []
        
    # Calculate player ratings
    player_ratings = {player: calculate_player_rating(performance, player) for player in players}
    
    # Sort players by rating
    sorted_players = sorted(players, key=lambda p: player_ratings[p], reverse=True)
    team1, team2 = [], []
    team1_rating, team2_rating = 0, 0

    # Use a snake draft approach for better balance
    for i, player in enumerate(sorted_players):
        if i % 2 == 0:
            if team1_rating <= team2_rating:
                team1.append(player)
                team1_rating += player_ratings[player]
            else:
                team2.append(player)
                team2_rating += player_ratings[player]
        else:
            if team2_rating <= team1_rating:
                team2.append(player)
                team2_rating += player_ratings[player]
            else:
                team1.append(player)
                team1_rating += player_ratings[player]
    
    # Store the teams in session state for history
    st.session_state.last_teams = {
        'team1': team1.copy(),
        'team2': team2.copy(),
        'team1_rating': team1_rating,
        'team2_rating': team2_rating
    }
    
    # Add to team history
    st.session_state.team_history.insert(0, {
        'team1': team1.copy(),
        'team2': team2.copy(),
        'team1_rating': team1_rating,
        'team2_rating': team2_rating,
        'timestamp': pd.Timestamp.now()
    })
    
    # Keep only the last 5 team generations in history
    if len(st.session_state.team_history) > 5:
        st.session_state.team_history = st.session_state.team_history[:5]
                
    return team1, team2

# Load data automatically when the app starts
if not st.session_state.player_data:
    with st.spinner("Loading data from file..."):
        st.session_state.player_data = load_player_data()
        if st.session_state.player_data:
            st.session_state.performance, st.session_state.synergy = analyze_stats(st.session_state.player_data)

# Display app content based on whether data was loaded
if st.session_state.player_data:
    st.success(f"✅ Data loaded successfully from '{DATA_FILE}'! Found {len(st.session_state.player_data)} players.")
    
    st.markdown('<h2 class="sub-header">Player Selection</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Player selection
        all_players = sorted(st.session_state.player_data.keys())
        
        # Create two columns for player selection
        select_col1, select_col2 = st.columns(2)
        
        with select_col1:
            st.markdown("**Available Players**")
            for player in all_players:
                if player not in st.session_state.selected_players:
                    perf = st.session_state.performance[player]
                    games = perf['games']
                    win_rate = (perf['wins'] + perf['draws'] * 0.5) / games if games > 0 else 0
                    
                    if st.button(f"➕ {player} ({win_rate:.0%})", key=f"add_{player}"):
                        if len(st.session_state.selected_players) < 10:
                            st.session_state.selected_players.append(player)
                            st.session_state.teams_generated = False
                            st.rerun()
                        else:
                            st.warning("Maximum of 10 players already selected")
        
        with select_col2:
            st.markdown("**Selected Players**")
            for player in st.session_state.selected_players:
                perf = st.session_state.performance[player]
                games = perf['games']
                win_rate = (perf['wins'] + perf['draws'] * 0.5) / games if games > 0 else 0
                
                if st.button(f"➖ {player} ({win_rate:.0%})", key=f"remove_{player}"):
                    st.session_state.selected_players.remove(player)
                    st.session_state.teams_generated = False
                    st.rerun()
        
        st.info(f"**{len(st.session_state.selected_players)} of 10 players selected**")
    
    with col2:
        # Action buttons
        st.markdown("**Actions**")
        if st.button("🔄 Randomly Select 10 Players", help="Randomly select 10 players"):
            if len(all_players) >= 10:
                st.session_state.selected_players = random.sample(all_players, 10)
                st.session_state.teams_generated = False
                st.rerun()
            else:
                st.error("Not enough players in the dataset")
        
        if st.button("🧹 Clear All Selections", help="Clear all selections"):
            st.session_state.selected_players = []
            st.session_state.teams_generated = False
            st.rerun()
            
        if st.button("📊 Generate Teams", disabled=len(st.session_state.selected_players) != 10,
                    help="Generate balanced teams from selected players"):
            st.session_state.team1, st.session_state.team2 = generate_teams(
                st.session_state.selected_players, 
                st.session_state.performance, 
                st.session_state.synergy
            )
            st.session_state.teams_generated = True
            st.rerun()
            
        if st.button("🔄 Regenerate Teams", disabled=not st.session_state.teams_generated,
                    help="Generate different teams with the same players"):
            # Shuffle the players slightly to get different combinations
            shuffled_players = st.session_state.selected_players.copy()
            random.shuffle(shuffled_players)
            
            st.session_state.team1, st.session_state.team2 = generate_teams(
                shuffled_players, 
                st.session_state.performance, 
                st.session_state.synergy
            )
            st.rerun()

    # Display player stats in an expander
    with st.expander("View Player Statistics"):
        stats_data = []
        for player in sorted(st.session_state.player_data.keys()):
            perf = st.session_state.performance[player]
            games = perf['games']
            if games > 0:
                win_rate = (perf['wins'] + perf['draws'] * 0.5) / games
                rating = calculate_player_rating(st.session_state.performance, player)
            else:
                win_rate = 0
                rating = 0
                
            stats_data.append({
                'Player': player,
                'Rating': rating,
                'Score': perf['score'],
                'Games': perf['games'],
                'Wins': perf['wins'],
                'Losses': perf['losses'],
                'Draws': perf['draws'],
                'Win Rate': win_rate
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(
            stats_df,
            use_container_width=True,
            column_config={
                "Player": st.column_config.TextColumn(width="medium"),
                "Rating": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=10),
                "Score": st.column_config.NumberColumn(format="%d"),
                "Games": st.column_config.NumberColumn(format="%d"),
                "Wins": st.column_config.NumberColumn(format="%d"),
                "Losses": st.column_config.NumberColumn(format="%d"),
                "Draws": st.column_config.NumberColumn(format="%d"),
                "Win Rate": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1)
            },
            hide_index=True
        )

    # Display generated teams at the bottom of the same tab
    if st.session_state.teams_generated:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">Generated Teams</h2>', unsafe_allow_html=True)
        
        # Calculate team stats
        team1_rating = sum(calculate_player_rating(st.session_state.performance, p) for p in st.session_state.team1)
        team2_rating = sum(calculate_player_rating(st.session_state.performance, p) for p in st.session_state.team2)
        rating_diff = abs(team1_rating - team2_rating)
        
        # Display teams side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="team-section">', unsafe_allow_html=True)
            st.markdown('<div class="team-header">🔴 Team Colours</div>', unsafe_allow_html=True)
            for player in st.session_state.team1:
                rating = calculate_player_rating(st.session_state.performance, player)
                st.markdown(f'<div class="team-red">{player} (Rating: {rating:.1f})</div>', unsafe_allow_html=True)
            st.markdown(f"**Total Rating: {team1_rating:.1f}**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="team-section">', unsafe_allow_html=True)
            st.markdown('<div class="team-header">⚪ Team White</div>', unsafe_allow_html=True)
            for player in st.session_state.team2:
                rating = calculate_player_rating(st.session_state.performance, player)
                st.markdown(f'<div class="team-white">{player} (Rating: {rating:.1f})</div>', unsafe_allow_html=True)
            st.markdown(f"**Total Rating: {team2_rating:.1f}**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Team balance indicator
        st.markdown("### ⚖️ Team Balance")
        if rating_diff <= 1.0:
            st.markdown(f'<p class="balance-good">**Excellent Balance** (Difference: {rating_diff:.1f})</p>', unsafe_allow_html=True)
        elif rating_diff <= 3.0:
            st.markdown(f'<p class="balance-fair">**Good Balance** (Difference: {rating_diff:.1f})</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="balance-poor">**Some Imbalance** (Difference: {rating_diff:.1f})</p>', unsafe_allow_html=True)

    # Display team history if available
    if st.session_state.team_history:
        with st.expander("View Recent Team History"):
            for i, history in enumerate(st.session_state.team_history):
                st.markdown(f"**Generation {i+1}** ({history['timestamp'].strftime('%Y-%m-%d %H:%M')})")
                
                hist_col1, hist_col2 = st.columns(2)
                with hist_col1:
                    st.markdown("**Team Colours**")
                    for player in history['team1']:
                        st.markdown(f"- {player}")
                    st.markdown(f"*Rating: {history['team1_rating']:.1f}*")
                
                with hist_col2:
                    st.markdown("**Team White**")
                    for player in history['team2']:
                        st.markdown(f"- {player}")
                    st.markdown(f"*Rating: {history['team2_rating']:.1f}*")
                
                st.markdown("---")

else:
    st.error(f"❌ Could not load data from '{DATA_FILE}'. Please make sure the file exists in the same directory as this app.")

# Instructions in sidebar
with st.sidebar:
    st.markdown("### 📋 Instructions")
    st.markdown("""
    1. Make sure **'thursday_football.xlsx'** is in the same directory
    2. Select **10 players** from the available list
    3. Click **'Generate Teams'** to create balanced teams
    4. View results at the **bottom of the page**
    """)
    
    st.markdown("### 📊 Excel Format")
    st.markdown("""
    - **First column**: Player names
    - **Other columns**: Match results
    - **Format**: `Team:Result` or just `Result`
    - **Teams**: R (Red), W (White), B (None)
    - **Results**: W (Win), D (Draw), L (Loss)
    
    Example: `R:W` = Red team, Win
    """)
    
    st.markdown("### 🔧 Actions")
    if st.button("🔄 Reload Data"):
        st.session_state.player_data = {}
        st.session_state.selected_players = []
        st.session_state.teams_generated = False
        st.session_state.team_history = []
        st.rerun()

# Add footer
st.markdown("---")
st.markdown("*5v5 Team Generator - Automatically creates balanced teams based on historical performance*")
