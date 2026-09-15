from scrapling import Fetcher

for slug in ['rey', 'luke-skywalker', 'darksaber', 'tatooine', 'x-wing-starfighter', 'r2-d2', 'death-star']:
    r = Fetcher.get(f'https://www.starwars.com/databank/{slug}')
    cats = {}
    for c in r.css('.stats-container .category'):
        h = c.css('.heading::text').get()
        v = c.css('.property-name::text').getall()
        cats[h] = v
    print(f"\n=== {slug.upper()} ===")
    print("Categories:", cats)
