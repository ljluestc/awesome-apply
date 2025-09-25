#!/usr/bin/env python3
"""
Analyze scraped JobRight.ai design data to extract key components
"""

import json
import re
from bs4 import BeautifulSoup

def analyze_jobright_design():
    """Analyze scraped design data and extract key components"""

    # Load the scraped design data
    with open('jobright_design_data.json', 'r', encoding='utf-8') as f:
        design_data = json.load(f)

    print("🔍 ANALYZING JOBRIGHT.AI DESIGN DATA")
    print("=" * 60)

    # Parse HTML structure
    soup = BeautifulSoup(design_data['html_structure'], 'html.parser')

    # Extract key color palette
    colors = design_data.get('colors', [])
    primary_colors = [color for color in colors if '#00f0a0' in color or '#52ffba' in color or '#00c98d' in color]

    print("🎨 PRIMARY COLOR PALETTE:")
    key_colors = {
        'primary': '#00f0a0',  # Main teal/mint
        'hover': '#52ffba',    # Lighter hover state
        'active': '#00c98d',   # Darker active state
        'background': '#ffffff',
        'text': '#000000',
        'secondary_text': 'rgba(0, 0, 0, 0.45)',
        'border': '#d9d9d9',
        'success': '#52c41a',
        'error': '#ff4d4f',
        'warning': '#faad14'
    }

    for name, color in key_colors.items():
        print(f"  {name}: {color}")

    # Extract typography
    fonts = design_data.get('fonts', [])
    primary_font = "__Inter_c3f87e,__Inter_Fallback_c3f87e"

    print(f"\n📝 TYPOGRAPHY:")
    print(f"  Primary Font: Inter (with fallback)")
    print(f"  Base Size: 14px")
    print(f"  Line Height: 1.5714285714285714")

    # Extract key CSS classes and styles
    css_content = design_data.get('css_styles', '')

    # Find Ant Design components being used
    ant_components = re.findall(r'\.ant-([a-zA-Z-]+)', css_content)
    unique_components = list(set(ant_components))[:20]  # Top 20 components

    print(f"\n🧩 ANT DESIGN COMPONENTS USED:")
    for i, component in enumerate(sorted(unique_components)):
        if i % 4 == 0:
            print()
        print(f"  ant-{component:<20}", end="")
    print()

    # Extract interactive elements
    interactive_elements = design_data.get('interactive_elements', [])

    print(f"\n🔘 INTERACTIVE ELEMENTS ({len(interactive_elements)} found):")
    for element in interactive_elements[:10]:  # Show first 10
        print(f"  • {element['tag']}: '{element['text'][:30]}...' ({element.get('classes', 'no-class')})")

    # Extract components
    components = design_data.get('components', [])

    print(f"\n🏗️ PAGE COMPONENTS ({len(components)} analyzed):")
    component_types = {}
    for comp in components:
        comp_type = comp['type']
        if comp_type not in component_types:
            component_types[comp_type] = 0
        component_types[comp_type] += 1

    for comp_type, count in component_types.items():
        print(f"  • {comp_type}: {count} instances")

    # Extract layout structure from HTML
    print(f"\n📐 LAYOUT ANALYSIS:")

    # Find main container structures
    main_containers = soup.find_all(['div'], class_=lambda x: x and ('container' in x or 'main' in x or 'layout' in x))
    print(f"  Main containers: {len(main_containers)}")

    # Find navigation elements
    nav_elements = soup.find_all(['nav', 'header']) + soup.find_all('div', class_=lambda x: x and 'nav' in x.lower())
    print(f"  Navigation elements: {len(nav_elements)}")

    # Find job listing elements
    job_elements = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
    print(f"  Job-related elements: {len(job_elements)}")

    # Find button elements
    buttons = soup.find_all(['button', 'a'], class_=lambda x: x and ('btn' in x or 'button' in x))
    print(f"  Button elements: {len(buttons)}")

    return {
        'colors': key_colors,
        'font': 'Inter',
        'components': unique_components,
        'interactive_count': len(interactive_elements),
        'layout_info': {
            'containers': len(main_containers),
            'navigation': len(nav_elements),
            'job_elements': len(job_elements),
            'buttons': len(buttons)
        }
    }

if __name__ == "__main__":
    analysis = analyze_jobright_design()

    print("\n" + "="*60)
    print("🎯 DESIGN ANALYSIS COMPLETE")
    print("Ready to build perfect JobRight.ai clone!")
    print("="*60)