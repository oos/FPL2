# FPL Application - Refactored Architecture

## Overview
This is a completely refactored Fantasy Premier League (FPL) application that has been transformed from a monolithic, hardcoded Python application into a modern, modular, object-oriented system with a Flask backend API and React frontend.

## Architecture

### Backend (Flask API)
- **Location**: `app.py`
- **Database**: SQLite (`fpl_oos.db`)
- **Port**: 5001 (changed from 5000 due to macOS AirPlay conflict)

#### Key Components
1. **DatabaseManager Class**: Handles all database operations
   - Player CRUD operations
   - Team management
   - Fixture data
   
2. **FPLDataManager Class**: Manages external FPL API calls
   - Team data fetching
   - Fixture difficulty ratings
   
3. **API Endpoints**:
   - `GET /api/players` - Get all players
   - `GET /api/players/<position>` - Get players by position
   - `GET /api/teams` - Get all teams
   - `GET /api/fixtures` - Get all fixtures
   - `GET /api/fdr` - Get fixture difficulty ratings
   - `POST /api/optimize-team` - Optimize team selection

### Frontend (React)
- **Location**: `fpl-frontend/`
- **Port**: 3000
- **Framework**: React 19 with TypeScript

#### Key Components
1. **API Service** (`src/services/api.ts`): Centralized API communication
2. **Pages**:
   - **Home**: Navigation hub and overview
   - **Players**: Comprehensive player analysis with filtering and sorting
   - **FDR**: Fixture difficulty ratings by gameweek
   - **Squad**: Optimal team selection with budget analysis

#### Features
- Responsive design with Bootstrap
- Real-time data fetching from Flask backend
- Interactive tables with sorting and filtering
- Charts and visualizations (Recharts)
- Error handling and loading states

## Database Schema

### Players Table
```sql
CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position_name TEXT NOT NULL,
    team TEXT NOT NULL,
    price REAL NOT NULL,
    availability TEXT DEFAULT 'Available',
    uncertainty_percent TEXT DEFAULT '24%',
    overall_total REAL NOT NULL,
    gw1_points REAL DEFAULT 0.0,
    gw2_points REAL DEFAULT 0.0,
    gw3_points REAL DEFAULT 0.0,
    gw4_points REAL DEFAULT 0.0,
    gw5_points REAL DEFAULT 0.0,
    gw6_points REAL DEFAULT 0.0,
    gw7_points REAL DEFAULT 0.0,
    gw8_points REAL DEFAULT 0.0,
    gw9_points REAL DEFAULT 0.0,
    points_per_million REAL DEFAULT 0.0,
    chance_of_playing_next_round INTEGER DEFAULT 100
);
```

## Setup and Installation

### Backend Setup
1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements_flask.txt
   ```

3. Run Flask backend:
   ```bash
   python3 app.py
   ```

### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd fpl-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start React development server:
   ```bash
   npm start
   ```

## Data Migration

The application includes migration scripts to move data from the old hardcoded structure:
- `simple_migrate.py`: Basic player data migration
- `add_more_players.py`: Additional player data

## Key Improvements

### Before (Old Architecture)
- ❌ Hardcoded data in Python files
- ❌ Monolithic structure
- ❌ No separation of concerns
- ❌ Difficult to maintain and extend
- ❌ No proper error handling
- ❌ Limited user interface

### After (New Architecture)
- ✅ Clean database-driven architecture
- ✅ Modular, object-oriented design
- ✅ RESTful API with proper error handling
- ✅ Modern React frontend with TypeScript
- ✅ Responsive and interactive UI
- ✅ Easy to maintain and extend
- ✅ Proper separation of concerns

## API Documentation

### Player Endpoints
- **GET /api/players**: Returns all players sorted by total points
- **GET /api/players/{position}**: Returns players filtered by position

### Team Optimization
- **POST /api/optimize-team**: Optimizes team selection based on budget and formation
  - Request body: `{"budget": 100.0, "formation": "4-4-2"}`
  - Returns: Optimized team with goalkeepers, defenders, midfielders, and forwards

### FDR Endpoints
- **GET /api/fdr**: Returns fixture difficulty ratings for all gameweeks

## Development

### Adding New Features
1. Add new database tables in `DatabaseManager.init_database()`
2. Create new API endpoints in `app.py`
3. Add corresponding frontend components and API calls
4. Update TypeScript interfaces in `api.ts`

### Database Changes
1. Modify the database schema in `DatabaseManager.init_database()`
2. Create migration scripts for existing data
3. Update the frontend to handle new data structures

## Testing

### Backend Testing
- Test API endpoints with curl or Postman
- Verify database operations
- Check error handling

### Frontend Testing
- Test React components in browser
- Verify API integration
- Test responsive design

## Deployment

### Production Build
1. Build React frontend:
   ```bash
   cd fpl-frontend
   npm run build
   ```

2. Serve static files from Flask backend
3. Configure production database
4. Set up proper CORS and security headers

## Future Enhancements

- [ ] User authentication and team management
- [ ] Real-time FPL data updates
- [ ] Advanced team optimization algorithms
- [ ] Player comparison tools
- [ ] Historical performance analysis
- [ ] Mobile app development
- [ ] Integration with FPL official API
- [ ] Machine learning for player performance prediction

## Troubleshooting

### Common Issues
1. **Port 5000 in use**: Change to port 5001 in `app.py`
2. **CORS errors**: Ensure Flask-CORS is properly configured
3. **Database connection issues**: Check file permissions for `fpl_oos.db`
4. **React build errors**: Clear `node_modules` and reinstall dependencies

### Logs
- Backend logs: Check Flask console output
- Frontend logs: Check browser console and React dev tools
- Database logs: Check SQLite database integrity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the established architecture
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
