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
        color: #2c3e50;
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
        color: #000000 !important; /* Ensure text is visible */
    }
    .team-white {
        background-color: #f5f5f5;
        border-left: 4px solid #9e9e9e;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #000000 !important; /* Ensure text is visible */
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
    st.session_state.performance = defaultdict(lambda: {'score': 0, 'games': 0})
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
                    if st.button(f"➕ {player}", key=f"add_{player}"):
                        if len(st.session_state.selected_players) < 10:
                            st.session_state.selected_players.append(player)
                            st.session_state.teams_generated = False
                            st.rerun()
                        else:
                            st.warning("Maximum of 10 players already selected")
        
        with select_col2:
            st.markdown("**Selected Players**")
            for player in st.session_state.selected_players:
                if st.button(f"➖ {player}", key=f"remove_{player}"):
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

    # Display player stats in an expander
    with st.expander("View Player Statistics"):
        stats_data = []
        for player in sorted(st.session_state.player_data.keys()):
            perf = st.session_state.performance[player]
            win_rate = (perf['score'] + perf['games']) / (2 * perf['games']) if perf['games'] > 0 else 0
            stats_data.append({
                'Player': player,
                'Score': perf['score'],
                'Games Played': perf['games'],
                'Win Rate': f"{win_rate:.1%}"
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(
            stats_df,
            use_container_width=True,
            column_config={
                "Player": st.column_config.TextColumn(width="medium"),
                "Score": st.column_config.NumberColumn(format="%d"),
                "Games Played": st.column_config.NumberColumn(format="%d"),
                "Win Rate": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1)
            },
            hide_index=True
        )

    # Display generated teams at the bottom of the same tab
    if st.session_state.teams_generated:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">Generated Teams</h2>', unsafe_allow_html=True)
        
        # Calculate team stats
        team1_score = sum(st.session_state.performance[p]['score'] for p in st.session_state.team1)
        team2_score = sum(st.session_state.performance[p]['score'] for p in st.session_state.team2)
        
        # Display teams side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="team-section">', unsafe_allow_html=True)
            st.markdown('<div class="team-header">🔴 Team Red</div>', unsafe_allow_html=True)
            for player in st.session_state.team1:
                st.markdown(f'<div class="team-red">{player}</div>', unsafe_allow_html=True)
            st.markdown(f"**Total Score: {team1_score}**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="team-section">', unsafe_allow_html=True)
            st.markdown('<div class="team-header">⚪ Team White</div>', unsafe_allow_html=True)
            for player in st.session_state.team2:
                st.markdown(f'<div class="team-white">{player}</div>', unsafe_allow_html=True)
            st.markdown(f"**Total Score: {team2_score}**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Team balance indicator
        balance_score = abs(team1_score - team2_score)
        st.markdown("### ⚖️ Team Balance")
        if balance_score <= 2:
            st.success(f"**Excellent Balance** (Difference: {balance_score})")
        elif balance_score <= 5:
            st.info(f"**Good Balance** (Difference: {balance_score})")
        else:
            st.warning(f"**Some Imbalance** (Difference: {balance_score})")

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
        st.rerun()

# Add footer
st.markdown("---")
st.markdown("*5v5 Team Generator - Automatically creates balanced teams based on historical performance*")
