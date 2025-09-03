# FPL Backend - Modular Architecture

This directory contains the refactored, object-oriented backend for the FPL application.

## Architecture Overview

The backend follows a clean, modular architecture with clear separation of concerns:

```
backend/
├── __init__.py              # Package initialization
├── app.py                   # Main Flask application factory
├── config.py                # Configuration management
├── models/                  # Data models
│   ├── __init__.py
│   ├── player.py           # Player model
│   ├── team.py             # Team model
│   └── fixture.py          # Fixture model
├── services/                # Business logic layer
│   ├── __init__.py
│   └── player_service.py   # Player business logic
├── routes/                  # API route definitions
│   ├── __init__.py
│   └── players.py          # Player API routes
├── database/                # Database management
│   ├── __init__.py
│   └── manager.py          # Database operations
└── utils/                   # Utility functions
    └── __init__.py
```

## Key Benefits

1. **Separation of Concerns**: Each module has a single responsibility
2. **Testability**: Services can be unit tested independently
3. **Maintainability**: Changes are isolated to specific modules
4. **Scalability**: Easy to add new features without touching existing code
5. **Clean Architecture**: Follows industry best practices

## Running the Backend

### Option 1: Use the launcher script
```bash
python3 run_backend.py
```

### Option 2: Run directly from backend directory
```bash
cd backend
python3 -m app
```

## Configuration

The application uses environment-based configuration:

- `FLASK_CONFIG`: Configuration profile (development, production, testing)
- `FLASK_DEBUG`: Enable/disable debug mode
- `PORT`: Server port (default: 5001)
- `DATABASE_PATH`: Path to SQLite database

## Database

The application uses SQLite with the following tables:

- **players**: Player information and statistics
- **teams**: Premier League team information
- **fixtures**: Fixture difficulty ratings (FDR)

## API Endpoints

### Legacy Endpoints (for backward compatibility)
- `GET /api/players` - Get all players
- `GET /api/players/<position>` - Get players by position
- `GET /api/teams` - Get all teams
- `GET /api/fdr` - Get fixture difficulty ratings

### New Modular Endpoints
- `GET /api/players/search/<query>` - Search players by name
- `GET /api/players/team/<team_name>` - Get players by team
- `GET /api/players/price-range` - Get players by price range
- `GET /api/players/top/points` - Get top players by points
- `GET /api/players/top/value` - Get top players by value
- `GET /api/players/statistics` - Get player statistics

### Health Check
- `GET /health` - Application health status

## Models

### Player Model
- Basic info: id, name, position, team, price
- Statistics: chance_of_playing_next_round, points_per_million, total_points, form, ownership
- Gameweek points: gw1_points through gw9_points
- Team relationship: team_id (foreign key)

### Team Model
- Basic info: id, name, short_name, code
- Metadata: strength, created_at

### Fixture Model
- Match info: home_team, away_team
- Difficulty ratings: home_difficulty, away_difficulty
- Scheduling: gameweek

## Services

### PlayerService
Handles all player-related business logic:
- Data retrieval and filtering
- Search functionality
- Statistics calculation
- Data validation and transformation

## Database Manager

The DatabaseManager class provides:
- Connection management with context managers
- Schema creation and validation
- CRUD operations for all models
- Database statistics and maintenance

## Migration from Old Structure

The refactoring maintains 100% backward compatibility:
- All existing API endpoints work exactly the same
- All existing functionality is preserved
- Templates and frontend code unchanged
- Database schema unchanged

## Future Enhancements

This modular structure makes it easy to add:
- User authentication and authorization
- Caching layer (Redis)
- Background task processing
- API rate limiting
- Comprehensive logging
- Unit and integration tests
