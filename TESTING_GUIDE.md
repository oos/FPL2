# 🧪 Testing Guide for Refactored FPL Backend

This guide shows you how to test the refactored backend to ensure everything works correctly.

## 🚀 **Quick Start Testing**

### **Option 1: Run Unit Tests (Fastest)**
```bash
python3 test_backend.py
```
This runs all unit tests without starting the server.

### **Option 2: Run Integration Tests (Most Comprehensive)**
```bash
python3 test_integration.py
```
This starts the server and tests all endpoints and pages.

### **Option 3: Manual Testing (Interactive)**
```bash
python3 run_backend.py
```
Then open your browser to `http://localhost:5001`

## 📋 **What Each Test Covers**

### **Unit Tests (`test_backend.py`)**
- ✅ **Model Classes**: Player, Team, Fixture creation and serialization
- ✅ **Database Operations**: CRUD operations, schema management
- ✅ **Service Layer**: Business logic, data processing
- ✅ **Flask App**: Application creation and configuration

### **Integration Tests (`test_integration.py`)**
- ✅ **API Endpoints**: All `/api/*` routes
- ✅ **Web Pages**: FDR, Players, and Squad pages
- ✅ **Server Startup**: Full application lifecycle
- ✅ **Data Flow**: End-to-end functionality

## 🔍 **Manual Testing Checklist**

### **1. Start the Backend**
```bash
python3 run_backend.py
```

### **2. Test API Endpoints**
Open a new terminal and test:

```bash
# Health check
curl http://localhost:5001/health

# Players API
curl http://localhost:5001/api/players

# Teams API  
curl http://localhost:5001/api/teams

# FDR API
curl http://localhost:5001/api/fdr
```

### **3. Test Web Pages**
Open your browser and navigate to:

- **FDR Page**: `http://localhost:5001/`
- **Players Page**: `http://localhost:5001/players`
- **Squad Page**: `http://localhost:5001/squad`

### **4. Verify Functionality**
For each page, check:

#### **FDR Page (`/`)**
- [ ] Page loads without errors
- [ ] GW tabs (ALL, GW1-GW9) are visible
- [ ] DataTables display fixture data
- [ ] FDR color coding works
- [ ] Filtering works correctly

#### **Players Page (`/players`)**
- [ ] Page loads without errors
- [ ] DataTable displays player data
- [ ] Position badges show correctly
- [ ] Filters work (position, team, price, etc.)
- [ ] Save/load views functionality works
- [ ] Sorting works (by points, value, etc.)

#### **Squad Page (`/squad`)**
- [ ] Page loads without errors
- [ ] GW tabs (GW1-GW9) are visible and clickable
- [ ] Squad summary displays correctly
- [ ] Captain management section works
- [ ] Transfer history shows
- [ ] Bench management displays

## 🐛 **Troubleshooting Common Issues**

### **Issue: "Module not found" errors**
**Solution**: Make sure you're running tests from the project root directory:
```bash
cd /Users/oos/FPL
python3 test_backend.py
```

### **Issue: Port 5001 already in use**
**Solution**: Kill existing processes or change port in `backend/config.py`:
```bash
pkill -f "python3 run_backend.py"
```

### **Issue: Database errors**
**Solution**: Check if `fpl_oos.db` exists and has data:
```bash
ls -la fpl_oos.db
sqlite3 fpl_oos.db ".tables"
```

### **Issue: Template not found errors**
**Solution**: Verify templates directory structure:
```bash
ls -la templates/
ls -la templates/fdr.html
```

## 📊 **Expected Test Results**

### **Unit Tests Should Show:**
```
🧪 Running Unit Tests...
test_player_creation (__main__.TestPlayerModel) ... ok
test_player_to_dict (__main__.TestPlayerModel) ... ok
test_player_from_db_row (__main__.TestPlayerModel) ... ok
test_team_creation (__main__.TestTeamModel) ... ok
test_team_to_dict (__main__.TestTeamModel) ... ok
test_fixture_creation (__main__.TestFixtureModel) ... ok
test_fixture_to_dict (__main__.TestFixtureModel) ... ok

✅ All unit tests passed!
```

### **Integration Tests Should Show:**
```
🌐 Testing API Endpoints...
✅ Health endpoint: PASS
✅ Players API endpoint: PASS
✅ Teams API endpoint: PASS
✅ FDR API endpoint: PASS

📄 Testing Web Pages...
✅ FDR page: PASS
✅ Players page: PASS
✅ Squad page: PASS

🎉 All integration tests passed! The backend is fully functional.
```

## 🔧 **Advanced Testing**

### **Test Specific Components**
```bash
# Test only models
cd backend
python3 -m unittest tests.test_models

# Test only database
python3 -c "
from database.manager import DatabaseManager
db = DatabaseManager(':memory:')
print('Database test:', 'PASS' if db else 'FAIL')
"
```

### **Performance Testing**
```bash
# Test API response times
time curl -s http://localhost:5001/api/players > /dev/null

# Test database query performance
python3 -c "
from backend.database.manager import DatabaseManager
import time
db = DatabaseManager()
start = time.time()
players = db.get_all_players()
end = time.time()
print(f'Query time: {(end-start)*1000:.2f}ms for {len(players)} players')
"
```

## 📝 **Test Report Template**

After running tests, document your results:

```markdown
## Test Report - [Date]

### Environment
- Python Version: [e.g., 3.11.0]
- Operating System: [e.g., macOS 14.0]
- Database: [e.g., fpl_oos.db with 500+ players]

### Test Results
- Unit Tests: [X/7] passed
- Integration Tests: [X/7] passed
- Manual Testing: [X/3] pages working

### Issues Found
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]

### Recommendations
- [Recommendation 1]
- [Recommendation 2]
```

## 🎯 **Success Criteria**

Your refactored backend is working correctly when:

1. ✅ **All unit tests pass** (7/7)
2. ✅ **All integration tests pass** (7/7)  
3. ✅ **All web pages load correctly** (3/3)
4. ✅ **All API endpoints return data** (4/4)
5. ✅ **No console errors** when running the server
6. ✅ **Database operations work** (CRUD, queries, stats)
7. ✅ **Frontend functionality preserved** (filters, tabs, DataTables)

## 🚨 **If Tests Fail**

1. **Check the error messages** - they usually point to the issue
2. **Verify file paths** - ensure all files are in the right locations
3. **Check Python path** - make sure imports work correctly
4. **Review database** - ensure schema and data are correct
5. **Check Flask configuration** - verify port and debug settings

## 🎉 **Celebration**

When all tests pass, you've successfully refactored your FPL application! The new modular architecture provides:

- **Better code organization**
- **Easier maintenance**
- **Professional development practices**
- **Foundation for future enhancements**

Happy testing! 🚀
