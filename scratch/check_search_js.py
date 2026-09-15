from scrapling import Fetcher
import re
import html
import json

r = Fetcher.get('https://www.starwars.com/databank')
print("Page length:", len(r.html_content))

# Look for data-module-data or data-json or window.__data
for m in re.finditer(r'data-module-data=[\'"]([^\'"]+)[\'"]', r.html_content):
    raw = html.unescape(m.group(1))
    print("\nFound data-module-data:", len(raw))
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            print("  Keys:", list(parsed.keys()))
            if 'data' in parsed:
                print("  Data len:", len(parsed['data']))
                if parsed['data'] and isinstance(parsed['data'], list):
                    print("  First item:", parsed['data'][0])
    except Exception as e:
        print("  Parse error:", e)

# Also check for inline scripts with JSON
for s in re.finditer(r'<script[^>]*>(.*?)</script>', r.html_content, re.DOTALL):
    content = s.group(1).strip()
    if 'Grill' in content or 'databank' in content.lower():
        if len(content) > 100 and len(content) < 2000:
            print("\nRelevant script:", content[:500])
