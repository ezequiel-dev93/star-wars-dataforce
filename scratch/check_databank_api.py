from scrapling import Fetcher
import re

r = Fetcher.get('https://www.starwars.com/databank')

# 1. Check for JSON endpoints or search
apis = set(re.findall(r'https?://[^\s"\'<>]*(?:api|search|datasource|matterhorn)[^\s"\'<>]*', r.html_content))
print("APIs found:")
for a in sorted(apis)[:10]:
    print(" ", a)

# 2. Check for __NEXT_DATA__ or inline JSON blocks
json_scripts = re.findall(r'<script[^>]*type=[\'"]application/json[\'"][^>]*>(.*?)</script>', r.html_content, re.DOTALL)
print(f"\nInline JSON scripts: {len(json_scripts)}")

# 3. Check for databank data references
data_refs = set(re.findall(r'[\w/-]+databank[\w/-]+', r.html_content, re.IGNORECASE))
print(f"\nDatabank terms: {len(data_refs)}")
for d in sorted(data_refs)[:15]:
    print(" ", d)
