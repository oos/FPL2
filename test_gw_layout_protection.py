#!/usr/bin/env python3
"""
Test to ensure GW2+ layout remains unchanged while working on GW1
This test captures the current working state and verifies it doesn't change
"""

import requests
import re
from bs4 import BeautifulSoup

def test_gw_layout_protection():
    """Test that GW2+ layouts remain unchanged"""
    
    # Get the current Squad Live page
    try:
        response = requests.get('http://localhost:5001/squad-live', timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"❌ Failed to fetch Squad Live page: {e}")
        return False
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Test results
    results = {
        'gw2_has_proper_table': False,
        'gw2_shows_position_names': False,
        'gw3_has_proper_table': False,
        'gw3_shows_position_names': False,
        'gw1_shows_position_names': False
    }
    
    # Check GW2 layout
    gw2_section = soup.find('div', {'id': 'gw2'})
    if gw2_section:
        # Check if GW2 has proper table structure
        gw2_table = gw2_section.find('table')
        if gw2_table:
            results['gw2_has_proper_table'] = True
            
            # Check if GW2 shows position names (Goalkeeper, Forward, etc.)
            position_badges = gw2_table.find_all('span', class_='badge bg-primary')
            for badge in position_badges:
                if badge.text.strip() in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']:
                    results['gw2_shows_position_names'] = True
                    break
    
    # Check GW3 layout
    gw3_section = soup.find('div', {'id': 'gw3'})
    if gw3_section:
        # Check if GW3 has proper table structure
        gw3_table = gw3_section.find('table')
        if gw3_table:
            results['gw3_has_proper_table'] = True
            
            # Check if GW3 shows position names
            position_badges = gw3_table.find_all('span', class_='badge bg-primary')
            for badge in position_badges:
                if badge.text.strip() in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']:
                    results['gw3_shows_position_names'] = True
                    break
    
    # Check GW1 layout (should show position names)
    gw1_section = soup.find('div', {'id': 'gw1'})
    if gw1_section:
        gw1_table = gw1_section.find('table')
        if gw1_table:
            # Check if GW1 shows position names (Goalkeeper, Forward, etc.)
            position_badges = gw1_table.find_all('span', class_='badge bg-primary')
            for badge in position_badges:
                if badge.text.strip() in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']:
                    results['gw1_shows_position_names'] = True
                    break
    
    # Print results
    print("🧪 GW Layout Protection Test Results:")
    print("=" * 50)
    print(f"GW2 has proper table: {'✅' if results['gw2_has_proper_table'] else '❌'}")
    print(f"GW2 shows position names: {'✅' if results['gw2_shows_position_names'] else '❌'}")
    print(f"GW3 has proper table: {'✅' if results['gw3_has_proper_table'] else '❌'}")
    print(f"GW3 shows position names: {'✅' if results['gw3_shows_position_names'] else '❌'}")
    print(f"GW1 shows position names: {'✅' if results['gw1_shows_position_names'] else '❌'}")
    
    # Overall result
    gw1_working = results['gw1_shows_position_names']
    gw2_working = results['gw2_has_proper_table'] and results['gw2_shows_position_names']
    gw3_working = results['gw3_has_proper_table'] and results['gw3_shows_position_names']
    
    if gw1_working and gw2_working and gw3_working:
        print("\n🎉 All GW layouts are working correctly!")
        return True
    else:
        print("\n⚠️ Some GW layouts have issues!")
        return False

if __name__ == "__main__":
    success = test_gw_layout_protection()
    exit(0 if success else 1)
