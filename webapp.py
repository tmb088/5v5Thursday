import streamlit as st
import pandas as pd
from collections import defaultdict
import random
import base64

# Set page configuration
st.set_page_config(
    page_title="5v5 Team Generator",
    page_icon="⚽",
    layout="wide"
)

# App title
st.title("⚽ 5v5 Team Generator")
st.markdown("Upload your Excel data file and select players to generate balanced teams.")

# Initialize session state
if 'player_data' not in st.session_state:
    st.session_state.player_data = {}
if 'performance' not in st.session_state:
    st.session_state.performance = defaultdict(lambda: {'score': 0, 'games': 0})
if 'synergy' not in st.session_state:
    st.session_state.synergy = defaultdict(lambda: defaultdict(int))
if 'selected_players' not in st.session_state:
    st.session_state.selected_players = []

# Add file format instructions
with st.expander("📋 Excel File Format Instructions"):
    st.markdown("""
    Your Excel file should follow this format:
    - **First column**: Player names
    - **Subsequent columns**: Match results using these codes:
    
    ### Team Codes (cell background color or first letter):
    - 🔴 **Red Team**: Use red cell background or prefix with `R:`
    - ⚪ **White Team**: Use no color/white background or prefix with `W:` (or no prefix)
    - ⚫ **Did Not Play**: Use black cell background or prefix with `B:`
    
    ### Result Codes (cell value):
    - ✅ **Win**: `W`
    - 🔄 **Draw**: `D`
    - ❌ **Loss**: `L`
    
    ### Examples:
    - A red team win: red cell background with `W` as value, or `R:W` in a cell
    - A white team loss: white cell background with `L` as value, or `L` (no prefix)
    - A black (did not play): black cell background with any value, or `B:W`
    """)
    
    # Provide a sample Excel file for download
    sample_data = {
        'Player': ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5'],
        'Match 1': ['R:W', 'R:W', 'W:W', 'B:L', 'W:L'],
        'Match 2': ['W:D', 'R:L', 'W:W', 'R:W', 'B:W'],
        'Match 3': ['R:W', 'W:L', 'R:D', 'W:W', 'R:W']
    }
    sample_df = pd.DataFrame(sample_data)
    
    # Convert sample DataFrame to Excel for download
    def to_excel(df):
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sample Data')
        writer.close()
        processed_data = output.getvalue()
        return processed_data
    
    excel_data = to_excel(sample_df)
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="sample_team_data.xlsx">📥 Download Sample Excel File</a>'
    st.markdown(href, unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])

def get_team_from_value(cell_value, cell_color=None):
    """
    Determine team from cell value or color
    For web version, we'll primarily use the value format (R:, W:, B:)
    """
    if pd.isna(cell_value):
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

def load_player_data(file):
    """Load player data from uploaded Excel file"""
    try:
        xls = pd.ExcelFile(file)
        df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
        
        player_data = {}
        for idx, row in df.iterrows():
            player = row.iloc[0]
            if pd.isna(player):
                continue
                
            player = str(player).strip()
            player_data[player] = []
            
            for cell in row[1:]:
                if pd.isna(cell):
                    player_data[player].append(('none', None))
                    continue
                    
                team, result = get_team_from_value(cell)
                player_data[player].append((team, result))
                
        return player_data
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
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

# Process uploaded file
if uploaded_file is not None:
    with st.spinner('Loading and analyzing data...'):
        st.session_state.player_data = load_player_data(uploaded_file)
        st.session_state.performance, st.session_state.synergy = analyze_stats(st.session_state.player_data)
    
    if st.session_state.player_data:
        st.success(f"Data loaded successfully! Found {len(st.session_state.player_data)} players.")
        
        # Player selection
        st.subheader("Select Players")
        all_players = sorted(st.session_state.player_data.keys())
        
        # Create two columns for player selection
        col1, col2 = st.columns(2)
        
        selected_players = []
        with col1:
            st.markdown("**Available Players**")
            for player in all_players:
                if player not in st.session_state.selected_players:
                    if st.button(f"➕ {player}", key=f"add_{player}"):
                        if len(st.session_state.selected_players) < 10:
                            st.session_state.selected_players.append(player)
                        else:
                            st.warning("Maximum of 10 players already selected")
                        st.rerun()
        
        with col2:
            st.markdown("**Selected Players**")
            for player in st.session_state.selected_players:
                if st.button(f"➖ {player}", key=f"remove_{player}"):
                    st.session_state.selected_players.remove(player)
                    st.rerun()
        
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
                    st.rerun()
                else:
                    st.error("Not enough players in the dataset")
        
        with col2:
            if st.button("🧹 Clear All", help="Clear all selections"):
                st.session_state.selected_players = []
                st.rerun()
                
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
        st.error("Failed to load player data from the uploaded file. Please check the file format.")
else:
    st.info("Please upload an Excel file to get started.")