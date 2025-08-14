# FPL Tools - Fixture Difficulty Ratings (FDR)

A clean, focused Flask application for displaying Fantasy Premier League Fixture Difficulty Ratings with opponent information.

## Features

- **FDR Table**: Complete fixture difficulty ratings for all 20 Premier League teams across 38 gameweeks
- **Color Coding**: Visual representation of fixture difficulty (1=Very Easy to 5=Very Hard)
- **Opponent Information**: Shows which team each team plays in each gameweek
- **Interactive Filters**: Filter by gameweek range and team name
- **Sortable Columns**: All columns are sortable using DataTables
- **Responsive Design**: Modern Bootstrap-based UI with mobile-friendly layout
- **Real-time Data**: Fetches latest fixture data from the official FPL API

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/oos/FPL2.git
   cd FPL2
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements_FPL_oos.txt
   ```

## Usage

1. **Start the application**:
   ```bash
   python3 FPL_oos.py
   ```

2. **Access the FDR table**:
   - Open your browser and go to `http://127.0.0.1:8003/`
   - The main page displays the complete FDR table

3. **Use the filters**:
   - **Gameweek Range**: Select specific gameweeks to view (e.g., GW1-10)
   - **Team Filter**: Search for specific teams (e.g., "Arsenal", "Chelsea")
   - **Apply Filters**: Click the "Apply Filters" button to update the view

## FDR Color Legend

- 🟢 **1 - Very Easy** (Dark Green): Favorable fixtures
- 🟢 **2 - Easy** (Light Green): Good fixtures
- ⚪ **3 - Medium** (Gray): Average difficulty
- 🔴 **4 - Hard** (Pink): Challenging fixtures
- 🔴 **5 - Very Hard** (Dark Red): Very difficult fixtures

## API Endpoints

- **`/`**: Main FDR table page
- **`/health`**: Health check endpoint (returns JSON status)

## Data Source

The application fetches real-time data from the official Fantasy Premier League API:
- **Teams**: `https://fantasy.premierleague.com/api/bootstrap-static/`
- **Fixtures**: `https://fantasy.premierleague.com/api/fixtures/`

## Database

FDR data is automatically saved to a local SQLite database (`fpl_fdr.db`) for caching and offline access.

## Technical Details

- **Framework**: Flask 3.1.1
- **Data Processing**: Pandas 2.3.1
- **UI**: Bootstrap 5.3.0 + DataTables 1.11.3
- **Styling**: Custom CSS with FDR color coding
- **Port**: Default port 8003 (configurable in code)

## Development

The application is structured with:
- Clean separation of concerns
- Modular functions for data fetching and processing
- Responsive HTML templates
- Error handling for API failures

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
