"""Build data/halifax_restaurants.json from a hand-curated list of real Halifax-area restaurants.

Names, addresses, coordinates, hours, phones and websites were cross-checked against
OpenStreetMap (see scripts/fetch_halifax.py) and the restaurants' public listings in late 2026.
Chains and closed places were left out. Restaurants change, so re-check before relying on hours.

Run:  python scripts/build_seed_data.py   then   python seed.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "halifax_restaurants.json"

PHOTO_BY_CUISINE = {
    "indian": [
        ("1585937421612-70a008356fbe", "Bowls of Indian curries garnished with herbs"),
        ("1565557623262-b51c2513a641", "Chicken curry with garlic naan"),
        ("1601050690597-df0568f70950", "Crispy samosas with green chilies"),
        ("1588166524941-3bf61a9c41db", "Paneer curry topped with fresh herbs"),
        ("1546833999-b9f581a1996d", "Biryani rice dish with spices"),
        ("1517248135467-4c7edcad34c4", "Restaurant dining room with warm lighting"),
    ],
    "italian": [
        ("1621996346565-e3dbc646d9a9", "Penne pasta in tomato sauce"),
        ("1574071318508-1cdbab80d002", "Wood-fired pizza with basil"),
        ("1595295333158-4742f28fbd85", "Spaghetti with seafood"),
        ("1551183053-bf91a1d81141", "Fresh pasta and sauce"),
        ("1414235077428-338989a2e8c0", "Restaurant table with Italian food"),
        ("1476224203421-9ac39bcb3327", "Pizza on a wooden board"),
    ],
    "japanese": [
        ("1611143669185-af224c5e3252", "Assorted sushi rolls and nigiri"),
        ("1569718212165-3a8278d5f624", "Ramen bowl with egg and green onions"),
        ("1617196034796-73dfa7b1fd56", "Nigiri sushi on a slate"),
        ("1579871494447-9811cf80d66c", "Sushi platter"),
        ("1553621042-f6e147245754", "Japanese restaurant dishes"),
    ],
    "chinese": [
        ("1563245372-f21724e3856d", "Steamed dumplings in bamboo baskets"),
        ("1585032226651-759b368d7246", "Stir-fried noodles with chopsticks"),
        ("1496116218417-1a781b1c416c", "Pan-fried dumplings"),
        ("1525755662778-989d0522089b", "Chinese takeout dishes"),
        ("1563379926898-05f4575a45d8", "Asian noodle soup"),
        ("1544025162-d76694265947", "Shared plates on a restaurant table"),
    ],
    "mexican": [
        ("1565299585323-38d6b0865b47", "Soft tacos with cilantro"),
        ("1599974579688-8dbdd335c77f", "Colourful vegetable tacos"),
        ("1626700051175-6818013e1d4f", "Burrito cut in half"),
        ("1552332386-f8dd00dc2f85", "Mexican street food"),
        ("1513456852971-30c0b8199d4d", "Tacos and salsa"),
    ],
    "thai": [
        ("1559314809-0d155014e29e", "Thai green curry with rice"),
        ("1562565652-a0d8f0c59eb4", "Pad Thai noodles"),
        ("1455619452474-d2be8b1e70cd", "Thai soup with herbs"),
        ("1546069901-ba9599a7e63c", "Colourful plated meal"),
    ],
    "middle-eastern": [
        ("1529006557811-74b19280a4dc", "Shawarma wrap and sides"),
        ("1544025162-d76694265947", "Grill platter with salads"),
        ("1601050690597-df0568f70950", "Fried appetizers with dips"),
        ("1555939594-58d7cb561ad1", "Wrap meal with fries"),
        ("1517248135467-4c7edcad34c4", "Warm restaurant interior"),
        ("1414235077428-338989a2e8c0", "Restaurant table setting"),
    ],
    "seafood": [
        ("1559339352-11d035aa65de", "Lobster dinner"),
        ("1559847844-5315695dadae", "Fish and chips"),
        ("1467003909585-2f5a4ba7b0f0", "Seafood platter"),
        ("1565299624946-b28f40a0ae38", "Fresh cooked seafood"),
        ("1476224203421-9ac39bcb3327", "Restaurant seafood dishes"),
        ("1414235077428-338989a2e8c0", "Fine dining table"),
        ("1559339352-11d035aa65de", "Lobster dinner"),
    ],
}

# name, cuisine, neighbourhood, address, lat, lng, price, dietary, phone, osm_hours, website, quality, description
R = [
    # Indian
    ("Naan N Curry", "indian", "West End", "6386 Quinpool Road", 44.64485, -63.59960, 2, "vegetarian,vegan,halal", "", "", "",
     4.5, "A Quinpool Road favourite that opened in 2019 and won The Coast's Best Indian Restaurant award. Big portions of butter chicken, vindaloo and fresh naan, with plenty of vegetarian dishes."),
    ("Mirchi Tandoor", "indian", "Downtown Halifax", "5232 Blowers Street", 44.64501, -63.57383, 2, "vegetarian,vegan", "+1-902-429-4647", "Tu-Su 11:00-23:00", "https://mirchitandoor.com/",
     4.3, "Late-night Indian and Indo-Chinese on Blowers Street, just off Argyle. Regulars order the lamb madras, tandoori platters and chilli chicken."),
    ("Rasa: Flavours of India", "indian", "Downtown Halifax", "1542 Birmingham Street", 44.64401, -63.57761, 2, "vegetarian,vegan", "", "", "",
     4.2, "A small spot steps from Spring Garden Road, handy for a quick curry lunch while you're out exploring downtown."),
    ("Masala Delight", "indian", "South End", "5361 Inglis Street", 44.63606, -63.57011, 2, "vegetarian,vegan", "+19024053320", "", "https://masaladelight.com",
     4.1, "A neighbourhood Indian kitchen in the South End near the universities. Comforting curries, biryani and thalis at student-friendly prices."),
    ("Swaad Sagaa", "indian", "North End", "5710 Young Street", 44.66045, -63.60088, 2, "vegetarian,vegan", "+1-902-399-6229", "Mo-Fr 12:00-21:00; Sa 16:00-21:00", "https://www.swaadsagaa.com/",
     4.3, "Home-style North Indian cooking near the Hydrostone, with a lunch crowd from nearby offices and the hospital."),
    ("Hyderabad Nawabs", "indian", "Clayton Park", "287 Lacewood Drive", 44.66404, -63.65861, 2, "vegetarian,halal", "", "", "",
     4.2, "Clayton Park's go-to for Hyderabadi dum biryani, haleem and spicy Andhra-style curries."),

    # Italian
    ("The Bicycle Thief", "italian", "Downtown Halifax", "1475 Lower Water Street", 44.64360, -63.56839, 3, "vegetarian", "+1 902-425-7993", "Mo-Su 11:30-23:00", "https://bicyclethief.ca/",
     4.6, "North American-Italian dining on the waterfront boardwalk, with a busy patio in summer. Known for handmade pasta, local seafood and its rich desserts."),
    ("Ristorante a Mano", "italian", "Downtown Halifax", "1477 Lower Water Street", 44.64380, -63.56925, 3, "vegetarian", "+1-902-423-6266", "Mo-Sa 11:30-22:00", "https://www.ristoranteamano.ca/",
     4.4, "Next door to Bicycle Thief on the harbour. Pasta is made by hand in-house, and the wood-fired pizza and harbour views make it a classic summer stop."),
    ("Da Zero Ristorante", "italian", "Downtown Halifax", "1472 Cathedral Lane", 44.64180, -63.58056, 3, "vegetarian,gluten-free", "+1 902-406-1210", "", "",
     4.6, "A cosy Italian dining room across from the Halifax Public Gardens, off Spring Garden Road. A good pick for date night: fresh pasta and a thoughtful wine list."),
    ("Pazzo Ristorante & Enoteca", "italian", "Downtown Halifax", "1566 Barrington Street", 44.64548, -63.57339, 3, "vegetarian", "", "Tu-Th 16:00-22:00; Fr-Sa 16:00-23:00; Su 16:00-21:00", "https://www.rcr.ca/restaurants/pazzo-italian-ristorante/",
     4.3, "One of downtown's newer Italian rooms on Barrington Street, with an enoteca-style wine program and classic pastas."),
    ("Il Mercato", "italian", "Bedford", "1595 Bedford Highway", 44.73336, -63.65415, 2, "vegetarian", "+1 9028324531", "Mo-Sa 11:00-22:00", "https://www.il-mercato.ca",
     4.3, "A long-time Bedford trattoria in Sunnyside Mall. Families and regulars come back for its classic pastas and authentic trattoria cooking."),
    ("Salvatore's Pizzaiolo Trattoria", "italian", "North End", "5541 Young Street", 44.66195, -63.59954, 2, "vegetarian", "+1-902-455-1133", "Mo 16:00-22:00; Tu-Sa 11:30-22:00", "https://www.salvatorespizza.ca",
     4.5, "A Hydrostone Market institution loved for its thin-crust pizza and relaxed trattoria feel."),
    ("Morris East", "italian", "Downtown Halifax", "5212 Morris Street", 44.64148, -63.57178, 2, "vegetarian", "+1-902-444-7663", "", "https://morriseast.com/",
     4.4, "Wood-fired pizza made with local ingredients, plus a cocktail list that draws a crowd on weekends."),
    ("La Piazza Ristorante", "italian", "West End", "6430 Chebucto Road", 44.64844, -63.60308, 2, "vegetarian", "+1 9024045885", "", "https://www.lapiazzarestocafe.com/",
     4.2, "A friendly West End spot known for its pizza, often voted among the city's best Italian in local reader polls."),

    # Japanese
    ("Dharma Sushi", "japanese", "Downtown Halifax", "1576 Argyle Street", 44.64537, -63.57407, 3, "gluten-free", "+1-902-425-7785", "Mo-Fr 11:45-14:15, 17:00-20:00", "https://dharmasushi.ca",
     4.4, "One of Halifax's longest-running sushi bars, serving the downtown crowd on Argyle Street since 1995."),
    ("Sushi Nami Royale", "japanese", "Downtown Halifax", "1458 Queen Street", 44.64245, -63.57574, 3, "vegetarian,gluten-free", "", "Mo-Th 11:30-22:00; Fr-Sa 11:30-23:00; Su 12:00-22:00", "https://sushinami.ca",
     4.5, "A big, polished sushi house that many locals call the best in town. Creative maki, sashimi boats and torched nigiri."),
    ("Wasabi House", "japanese", "West End", "6403 Quinpool Road", 44.64463, -63.60051, 2, "vegetarian", "", "We-Mo 11:00-22:00", "http://www.wasabihouse.ca/",
     4.3, "One of the most popular sushi spots on Quinpool Road. It's busy with students and families most nights."),
    ("Buta Ramen", "japanese", "Downtown Halifax", "5190 Morris Street", 44.64173, -63.57092, 2, "", "", "", "",
     4.5, "Halifax's best-known ramen shop, in the former Hamachi House space on Morris Street. Noodles are made in-house, and the tonkotsu is a winter staple."),
    ("Hamachi Kita", "japanese", "North End", "5537 Young Street", 44.66200, -63.59951, 3, "gluten-free", "", "Mo-We 11:00-20:00; Th 11:00-21:00; Fr 11:00-22:00; Sa 12:00-21:00", "https://www.hamachikita.com",
     4.2, "The North End outpost of a local Japanese group, tucked into the Hydrostone Market. Sushi, rolls and Japanese plates."),
    ("Tako Sushi & Ramen", "japanese", "Clayton Park", "480 Parkland Drive", 44.67094, -63.67643, 2, "vegetarian", "+1 902-405-8855", "Mo-Sa 11:00-21:00; Su 12:00-21:00", "https://www.takosushiramen.ca",
     4.4, "A Clayton Park neighbourhood favourite that does both sushi and ramen well. Great for takeout after a day at the park."),

    # Chinese
    ("Great Wall Restaurant", "chinese", "Downtown Halifax", "1649 Bedford Row", 44.64708, -63.57165, 2, "vegetarian", "+1 902-422-6153", "Mo-Fr 11:30-22:00; Sa-Su 16:00-22:00", "http://www.thegreatwall.ca/",
     4.4, "Open since 1984 and a regular winner of The Coast's Best Chinese vote. The dim sum lunch draws crowds, so expect a wait on weekends."),
    ("Look Ho Ho", "chinese", "West End", "6420 Bayers Road", 44.65448, -63.61069, 1, "vegetarian", "+1 902-455-5479", "Mo-Th,Su 11:30-23:00; Fr,Sa 11:30-24:00", "https://www.lookhoho.com/",
     4.3, "A Bayers Road institution serving Chinese-Canadian classics for decades. Regulars swear it has the best egg rolls in the Maritimes."),
    ("May Garden", "chinese", "Dartmouth", "136 Portland Street", 44.66690, -63.56481, 2, "vegetarian,vegan", "+1-902-469-2226", "", "https://maygarden.ca",
     4.3, "Downtown Dartmouth's Chinese restaurant since 1976. Chinese-Canadian staples, Szechuan dishes and Singapore noodles, with dim sum on weekends."),
    ("Fan's Chinese Restaurant", "chinese", "Dartmouth", "451 Windmill Road", 44.68500, -63.59938, 2, "vegetarian", "+1-902-469-9165", "Mo, We-Su 11:00-21:00", "https://www.fansrestaurant.ca/",
     4.4, "A Northern Chinese specialist on Windmill Road. Locals rate its ginger beef and black bean chicken among the best around the harbour."),
    ("9 + Nine", "chinese", "Clayton Park", "480 Parkland Drive", 44.67083, -63.67640, 2, "vegetarian,vegan", "", "Mo,We-Fr 09:00-14:00,17:00-21:00; Sa 11:30-14:00,16:30-21:00; Su 16:30-21:00", "https://9plus9.ca/",
     4.2, "A lighter, less greasy take on Chinese food in Clayton Park, with dumplings and noodle dishes."),
    ("Jean's Chinese Restaurant", "chinese", "Dartmouth", "516 Pleasant Street", 44.64539, -63.54325, 2, "vegetarian", "+1 902-444-7776", "", "https://www.jeansrestaurant.ca/",
     4.1, "A Woodside neighbourhood spot in south Dartmouth that does dependable Chinese takeout and sit-down family dinners."),

    # Mexican
    ("Antojo Tacos + Tequila", "mexican", "Downtown Halifax", "1667 Argyle Street", 44.64664, -63.57439, 2, "vegetarian,gluten-free", "+1 902 405 2790", "", "https://antojo.ca",
     4.3, "A lively Argyle Street taqueria with a big tequila list. Tacos, burritos and nachos are made to share."),
    ("Burrito Jax", "mexican", "Downtown Halifax", "5215 Blowers Street", 44.64528, -63.57349, 1, "vegetarian", "", "", "",
     4.2, "A downtown burrito counter on Blowers Street that has picked up plenty of Best of Halifax awards. Huge, cheap burritos and a late-night crowd."),
    ("Habanero's Modern Taco Bar", "mexican", "Downtown Halifax", "1551 South Park Street", 44.64347, -63.58003, 1, "vegetarian,gluten-free", "", "", "",
     4.2, "A fast, colourful taco bar near Spring Garden Road. Gold winner for The Coast's Best Burrito."),
    ("Tako Loco", "mexican", "North End", "3248 Isleville Street", 44.66368, -63.60321, 1, "vegetarian,gluten-free", "+1-902-420-1759", "Tu-Th 11:00-20:00; Fr,Sa 11:00-21:00", "",
     4.4, "A small, family-run North End taqueria tucked away on Isleville Street. Simple, authentic tacos and quesadillas."),
    ("Taco Land", "mexican", "Bedford", "1658 Bedford Highway", 44.73792, -63.65647, 1, "vegetarian", "", "Mo-Th 11:00-21:00; Fr,Sa 11:00-23:00; Su 12:00-20:00", "",
     4.0, "A casual taco joint on the Bedford Highway, good for a quick bite near the Basin."),

    # Thai
    ("Cha Baa Thai", "thai", "Downtown Halifax", "1546 Queen Street", 44.64402, -63.57707, 2, "vegetarian,vegan,gluten-free", "+1-902-406-3008", "", "https://www.chabaathairestaurant.ca/",
     4.5, "Voted Halifax's best Thai in The Coast several years running. A downtown flagship with sister locations in Dartmouth, Bedford and the North End."),
    ("Talay Thai", "thai", "South End", "5164 Morris Street", 44.64191, -63.57020, 2, "vegetarian,vegan,gluten-free", "", "", "",
     4.4, "A long-time favourite, and plenty of locals say it's their favourite Thai in town. Fragrant curries, noodles and seafood dishes."),
    ("Kajohn Thai", "thai", "North End", "6140 Young Street", 44.65792, -63.60379, 2, "vegetarian,vegan", "+1-902-443-8424", "Mo-Su 10:00-22:00", "https://www.kajohnthairestaurant.ca",
     4.2, "A relaxed North End Thai restaurant on Young Street. Generous curries and noodles at fair prices."),
    ("Baan Thai", "thai", "Downtown Halifax", "5234 Blowers Street", 44.64500, -63.57390, 2, "vegetarian,vegan,gluten-free", "+1 902-446-4301", "", "",
     4.1, "A cosy, long-running Thai room on Blowers Street, just off Argyle."),

    # Middle Eastern
    ("King of Donair", "middle-eastern", "West End", "6422 Quinpool Road", 44.64424, -63.60084, 1, "", "+1 902-421-0000", "", "https://www.kingofdonair.ca",
     4.3, "The Quinpool Road shop that has served Halifax-style donairs since 1973, with sweet garlic sauce and all. Repeat Best Donair winner. Brave souls try the two-pound donair."),
    ("Tony's Famous Pizza & Donair", "middle-eastern", "North End", "2390 Robie Street", 44.65091, -63.59264, 1, "", "", "Su-Tu 11:00-02:00; We,Th 11:00-03:00; Fr,Sa 11:00-04:00", "https://www.tonysdonair.ca/",
     4.2, "A late-night Robie Street legend and gold winner for Best Donair in 2024. A rite of passage after a night out."),
    ("Mezza Lebanese Kitchen", "middle-eastern", "Bedford", "14 Peakview Way", 44.70014, -63.68729, 1, "vegetarian,halal,gluten-free", "+1 902-429-2929", "", "https://www.mezzalebanesekitchen.com/",
     4.2, "A homegrown Lebanese chain that started in Halifax. Shawarma platters, fattoush and a halal, gluten-free donair."),
    ("Tarek's Cafe", "middle-eastern", "North End", "3045 Robie Street", 44.65926, -63.60091, 1, "vegetarian", "+1-902-454-8723", "Mo-Sa 11:30-19:30", "http://www.tarekscafe.ca/",
     4.5, "A family-run Lebanese cafe on north Robie. Falafel, shawarma and homestyle plates at very fair prices."),
    ("Chef Abod", "middle-eastern", "North End", "3217 Kempt Road", 44.66041, -63.60610, 1, "vegetarian,halal", "", "Mo-Th 11:00-20:30; Fr,Sa 11:00-21:00; Su 14:00-21:00", "",
     4.6, "A Middle Eastern kitchen on Kempt Road with a loyal following for its shawarma, grilled meats and sweets."),
    ("Efendy Turkish & Mediterranean Grill", "middle-eastern", "Downtown Halifax", "1569 Dresden Row", 44.64436, -63.57850, 2, "vegetarian,halal", "", "", "http://www.efendyrestaurant.com/",
     4.3, "Turkish grill on Dresden Row, just off Spring Garden Road. Grilled kebabs, Turkish plates and Turkish coffee."),

    # Seafood
    ("The Five Fishermen", "seafood", "Downtown Halifax", "1740 Argyle Street", 44.64785, -63.57538, 4, "gluten-free", "", "", "",
     4.7, "Fine dining in a historic building on Argyle Street, and one of the city's top-rated restaurants. Lobster, oysters and Atlantic fish."),
    ("Waterfront Warehouse", "seafood", "Downtown Halifax", "1549 Lower Water Street", 44.64584, -63.56994, 3, "gluten-free", "+19024257610", "Su-Th 11:30-21:00; Fr,Sa 11:30-22:00", "https://www.rcr.ca/restaurants/waterfront-warehouse/",
     4.4, "Halifax's seafood go-to since 1996, in an old warehouse on the boardwalk. Local oysters, live lobster from the tanks and a patio over the harbour."),
    ("Shuck Seafood + Raw Bar", "seafood", "Downtown Halifax", "5120 Salter Street", 44.64511, -63.57061, 3, "gluten-free", "+1-902-429-5120", "", "https://www.rcr.ca/restaurants/shuck-seafood-raw-bar/",
     4.5, "A raw bar a block from the waterfront, built around Nova Scotia oysters, crudo, ceviche and lobster rolls."),
    ("Sea Smoke Restaurant & Bar", "seafood", "Downtown Halifax", "1477 Lower Water Street", 44.64417, -63.56848, 3, "gluten-free", "", "", "https://www.seasmokehalifax.com",
     4.3, "An upper-level patio on the boardwalk with some of the best harbour views in the city. Seafood, sushi and cocktails."),
    ("Salt + Ash", "seafood", "Downtown Halifax", "1741 Lower Water Street", 44.64883, -63.57111, 2, "gluten-free", "", "", "",
     4.4, "A beach-house restaurant at Queen's Marque, where almost everything is cooked over a wood-fire hearth. Chowder, a crab-and-lobster 'crobster' roll and local beer on tap."),
    ("McKelvie's", "seafood", "Downtown Halifax", "1680 Lower Water Street", 44.64762, -63.57190, 3, "gluten-free", "", "", "",
     4.3, "A classic Halifax seafood house in a converted old firehall near the waterfront. Seafood chowder, haddock and lobster dinners."),
    ("Fries & Co.", "seafood", "West End", "2603 Connolly Street", 44.64826, -63.60479, 1, "", "", "", "",
     4.4, "A no-frills fish and chip shop off Quinpool that's been frying haddock for generations of Haligonians. Always busy at lunch."),
]

DAYS = {"Mo": "Mon", "Tu": "Tue", "We": "Wed", "Th": "Thu", "Fr": "Fri", "Sa": "Sat", "Su": "Sun"}


def pretty_hours(raw: str) -> str:
    """Turn OSM opening_hours like 'Mo-Fr 11:00-22:00; Sa 12:00-21:00' into readable text."""
    if not raw:
        return "Hours vary by season. Call ahead or check online."
    text = re.sub(r"\b(Mo|Tu|We|Th|Fr|Sa|Su)\b", lambda m: DAYS[m.group(1)], raw)
    text = re.sub(r"(\d{2}):(\d{2})", lambda m: _clock(int(m.group(1)), int(m.group(2))), text)
    text = text.replace("-", "–").replace(";", " ·").replace(",", ", ").replace(",  ", ", ")
    return text


def _clock(h: int, m: int) -> str:
    if h in (0, 24):
        return "midnight" if m == 0 else f"12:{m:02d} am"
    suffix = "am" if h < 12 or h >= 24 else "pm"
    h12 = h % 12 or 12
    if h > 24:
        h12 = h - 24
        suffix = "am"
    return f"{h12}{'' if m == 0 else f':{m:02d}'} {suffix}"


def pretty_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        return ""
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def main():
    out = []
    counters: dict[str, int] = {}
    for (name, cuisine, hood, addr, lat, lng, price, diet, phone, hours, site, quality, desc) in R:
        i = counters.get(cuisine, 0)
        counters[cuisine] = i + 1
        photo_id, alt = PHOTO_BY_CUISINE[cuisine][i % len(PHOTO_BY_CUISINE[cuisine])]
        out.append(
            {
                "name": name,
                "cuisine": cuisine,
                "neighbourhood": hood,
                "address": addr,
                "lat": lat,
                "lng": lng,
                "price_level": price,
                "dietary": diet,
                "phone": pretty_phone(phone),
                "hours": pretty_hours(hours),
                "description": desc,
                "website": site,
                "photo_id": photo_id,
                "photo_alt": alt,
                "quality": quality,
            }
        )
    out.sort(key=lambda r: (r["cuisine"], r["name"]))
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(out)} restaurants to {OUT}")
    print(counters)


if __name__ == "__main__":
    main()
