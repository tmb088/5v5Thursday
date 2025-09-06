# --- FULL CODE WITH BALANCED TEAMS AND SYNERGY WEIGHT ---

import streamlit as st
import pandas as pd
from collections import defaultdict
import random
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="5v5 Team Generator",
    page_icon="⚽",
    layout="wide"
)

# --- Custom CSS Styling ---
st.markdown("""<style>
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
    .team-header {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #2c3e50 !important;
    }
</style>""", unsafe_allow_html=True)

# --- App Title ---
st.markdown('<h1 class="main-header">⚽ 5v5 Team Generator</h1>', unsafe_allow_html=True)

# --- Session State Initialization ---
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

# --- File Constants ---
DATA_FILE = "thursday_football.xlsx"

# --- Helper Functions ---
def get_team_from_value(cell_value):
    if pd.isna(cell_value):
        return 'none', None
    cell_value = str(cell_value).strip().upper()
    if cell_value.startswith('R:'):
        return 'red', cell_value[2:]
    elif cell_value.startswith('W:'):
        return 'white', cell_value[2:]
    elif cell_value.startswith('B:'):
        return 'none', cell_value[2:]
    else:
        return 'white', cell_value

def load_player_data():
    if not os.path.exists(DATA_FILE):
        st.error(f"Data file '{DATA_FILE}' not found.")
        return {}
    df = pd.read_excel(DATA_FILE)
    player_data = {}
    for idx, row in df.iterrows():
        player = str(row.iloc[0]).strip()
        if not player or pd.isna(player):
            continue
        player_data[player] = []
        for cell in row[1:]:
            team, result = get_team_from_value(cell)
            player_data[player].append((team, result))
    return player_data

def analyze_stats(player_data):
    performance = defaultdict(lambda: {'score': 0, 'games': 0})
    synergy = defaultdict(lambda: defaultdict(int))
    num_days = max(len(games) for games in player_data.values())
    for day in range(num_days):
        red_team = []
        for player, games in player_data.items():
            if day >= len(games):
                continue
            team, result = games[day]
            if result in ['W', 'D', 'L']:
                performance[player]['games'] += 1
                performance[player]['score'] += {'W': 1, 'D': 0, 'L': -1}[result]
                if team == 'red':
                    red_team.append(player)
        for i, p1 in enumerate(red_team):
            for p2 in red_team[i+1:]:
                synergy[p1][p2] += 1
                synergy[p2][p1] += 1
    return performance, synergy

def generate_teams(players, performance, synergy, synergy_weight=1.0):
    if not players:
        return [], []
    sorted_players = sorted(players, key=lambda p: performance[p]['score'] / max(1, performance[p]['games']), reverse=True)
    team1, team2 = [], []
    team1_score, team2_score = 0, 0
    for player in sorted_players:
        avg_score = performance[player]['score'] / max(1, performance[player]['games'])
        synergy_with_team1 = sum(synergy[player][p] for p in team1)
        synergy_with_team2 = sum(synergy[player][p] for p in team2)
        penalty_team1 = synergy_with_team1 * synergy_weight + abs((team1_score + avg_score) - team2_score)
        penalty_team2 = synergy_with_team2 * synergy_weight + abs((team2_score + avg_score) - team1_score)
        if len(team1) < 5 and (len(team2) >= 5 or penalty_team1 < penalty_team2):
            team1.append(player)
            team1_score += avg_score
        else:
            team2.append(player)
            team2_score += avg_score
    return team1, team2

# --- Load Data ---
if not st.session_state.player_data:
    with st.spinner("Loading data..."):
        st.session_state.player_data = load_player_data()
        if st.session_state.player_data:
            st.session_state.performance, st.session_state.synergy = analyze_stats(st.session_state.player_data)

# --- Main App Logic ---
if st.session_state.player_data:
    st.success(f"✅ Data loaded from '{DATA_FILE}'")

    st.markdown('<h2 class="sub-header">Player Selection</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    all_players = sorted(st.session_state.player_data.keys())

    with col1:
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
                            st.warning("Maximum of 10 players")
        with select_col2:
            st.markdown("**Selected Players**")
            for player in st.session_state.selected_players:
                if st.button(f"➖ {player}", key=f"remove_{player}"):
                    st.session_state.selected_players.remove(player)
                    st.session_state.teams_generated = False
                    st.rerun()
        st.info(f"**{len(st.session_state.selected_players)} of 10 players selected**")

    with col2:
        st.markdown("**Actions**")
        if st.button("🔄 Randomly Select 10 Players"):
            if len(all_players) >= 10:
                st.session_state.selected_players = random.sample(all_players, 10)
                st.session_state.teams_generated = False
                st.rerun()
        if st.button("🧹 Clear All Selections"):
            st.session_state.selected_players = []
            st.session_state.teams_generated = False
            st.rerun()

        synergy_weight = st.slider("Synergy Weight", 0.0, 2.0, 1.0, 0.1)
        if st.button("📊 Generate Teams", disabled=len(st.session_state.selected_players) != 10):
            st.session_state.team1, st.session_state.team2 = generate_teams(
                st.session_state.selected_players,
                st.session_state.performance,
                st.session_state.synergy,
                synergy_weight
            )
            st.session_state.teams_generated = True
            st.rerun()

    with st.expander("View Player Statistics"):
        stats_data = []
        for player in sorted(all_players):
            perf = st.session_state.performance[player]
            win_rate = (perf['score'] + perf['games']) / (2 * perf['games']) if perf['games'] > 0 else 0
            stats_data.append({
                'Player': player,
                'Score': perf['score'],
                'Games Played': perf['games'],
                'Win Rate': f"{win_rate:.1%}"
            })
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True)

    if st.session_state.teams_generated:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">Generated Teams</h2>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        team1, team2 = st.session_state.team1, st.session_state.team2
        score1 = sum(st.session_state.performance[p]['score'] / max(1, st.session_state.performance[p]['games']) for p in team1)
        score2 = sum(st.session_state.performance[p]['score'] / max(1, st.session_state.performance[p]['games']) for p in team2)
        avg1, avg2 = score1 / 5, score2 / 5

        with col1:
            st.markdown('<div class="team-section"><div class="team-header">🔴 Team Colours</div>', unsafe_allow_html=True)
            for p in team1:
                st.markdown(f'<div class="team-red">{p}</div>', unsafe_allow_html=True)
            st.markdown(f"**Total Score: {score1:.2f}**  \n**Avg Rating: {avg1:.2f}**")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="team-section"><div class="team-header">⚪ Team White</div>', unsafe_allow_html=True)
            for p in team2:
                st.markdown(f'<div class="team-white">{p}</div>', unsafe_allow_html=True)
            st.markdown(f"**Total Score: {score2:.2f}**  \n**Avg Rating: {avg2:.2f}**")
            st.markdown('</div>', unsafe_allow_html=True)

        balance_diff = abs(score1 - score2)
        st.markdown("### ⚖️ Team Balance")
        if balance_diff <= 2:
            st.success(f"**Excellent Balance** (Difference: {balance_diff:.2f})")
        elif balance_diff <= 5:
            st.info(f"**Good Balance** (Difference: {balance_diff:.2f})")
        else:
            st.warning(f"**Some Imbalance** (Difference: {balance_diff:.2f})")

else:
    st.error(f"❌ Could not load data from '{DATA_FILE}'.")

# --- Sidebar Instructions ---
with st.sidebar:
    st.markdown("### 📋 Instructions")
    st.markdown("""
    1. Make sure **'thursday_football.xlsx'** is in the same folder
    2. Select **10 players**
    3. Adjust **synergy weight** to tune team balance
    4. Click **'Generate Teams'**
    """)
    st.markdown("### 📊 Excel Format")
    st.markdown("""
    - **First column**: Player names  
    - **Other columns**: Results like `R:W`, `W:L`, or `B:D`
    - **R/W/B** = Red/White/Bench
    - **W/D/L** = Win/Draw/Loss
    """)
    if st.button("🔄 Reload Data"):
        st.session_state.player_data = {}
        st.session_state.selected_players = []
        st.session_state.teams_generated = False
        st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("*Built to balance 5v5 teams using historical performance and player synergy.*")
