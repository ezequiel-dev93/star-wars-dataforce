"""
Catálogo de personajes por serie y película de Star Wars.

Define producciones Live-Action (permitidas) y Animadas (excluidas para evitar
descarga de ilustraciones/dibujos y enfocar el dataset en imagen real).
"""
from __future__ import annotations

# Series y películas Live-Action con listas de personajes clave
LIVE_ACTION_PRODUCTIONS: dict[str, list[str]] = {
    "the-mandalorian": [
        "The Mandalorian",  # Din Djarin
        "Grogu",
        "Boba Fett",
        "Fennec Shand",
        "Moff Gideon",
        "Bo-Katan Kryze",
        "Cara Dune",
        "Greef Karga",
        "The Armorer",
        "Paz Vizsla",
        "Dr. Pershing",
        "Cobb Vanth",
        "Bib Fortuna",
        "Peli Motto",
        "Axe Woves",
        "Koska Reeves",
        "Migs Mayfeld",
        "Kuiil",
        "IG-11",
        "The Client",
    ],
    "the-book-of-boba-fett": [
        "Boba Fett",
        "Fennec Shand",
        "The Mandalorian",
        "Grogu",
        "Cad Bane",
        "Black Krrsantan",
        "Mok Shaiz",
        "Garsa Fwip",
        "Drash",
        "Skad",
        "8D8",
        "Cobb Vanth",
        "Peli Motto",
        "Luke Skywalker",
        "Ahsoka Tano",
    ],
    "andor": [
        "Cassian Andor",
        "Bix Caleen",
        "Luthen Rael",
        "Mon Mothma",
        "Syril Karn",
        "Dedra Meero",
        "Vel Sartha",
        "Cinta Kaz",
        "Maarva Andor",
        "Brasso",
        "Kino Loy",
        "Ruescott Melshi",
        "Saw Gerrera",
        "Wilhuff Tarkin",
        "Orson Krennic",
    ],
    "obi-wan-kenobi": [
        "Obi-Wan Kenobi",
        "Darth Vader",
        "Reva Sevander",
        "Grand Inquisitor",
        "Fifth Brother",
        "Fourth Sister",
        "Tala Durith",
        "Nari",
        "Haja Estree",
        "Roken",
        "Princess Leia Organa",
        "Owen Lars",
        "Beru Lars",
        "Bail Organa",
    ],
    "ahsoka": [
        "Ahsoka Tano",
        "Sabine Wren",
        "Baylan Skoll",
        "Shin Hati",
        "Hera Syndulla",
        "Ezra Bridger",
        "Grand Admiral Thrawn",
        "Morgan Elsbeth",
        "Anakin Skywalker",
        "Chopper",
        "Mon Mothma",
        "Huyang",
        "Marrok",
        "Carson Teva",
        "Hamato Xiono",
        "Jai Kell",
        "Ryder Azadi",
    ],
    "the-acolyte": [
        "Mae Aniseya",
        "Osha Aniseya",
        "Master Sol",
        "Master Indara",
        "Master Kelnacca",
        "Master Torbin",
        "Qimir",
        "Vernestra Rwoh",
        "Jecki Lon",
        "Yord Fandar",
        "Mother Aniseya",
        "Mother Koril",
        "The Stranger",
        "Bazil",
    ],
    "star-wars-skeleton-crew": [
        "Wim",
        "Neel",
        "KB",
        "Fern",
        "Jod Na Nawood",
        "SM-33",
        "Wendle",
        "Fara",
        "Kh'ymm",
        "Pokkit",
        "Vane",
        "Tak Rennod",
        "Brutus",
    ],
    # Películas Live-Action
    "rogue-one": [
        "Jyn Erso",
        "Cassian Andor",
        "K-2SO",
        "Chirrut Îmwe",
        "Baze Malbus",
        "Bodhi Rook",
        "Orson Krennic",
        "Galen Erso",
        "Saw Gerrera",
        "Bail Organa",
        "Mon Mothma",
        "Grand Moff Tarkin",
    ],
    "solo": [
        "Han Solo",
        "Chewbacca",
        "Lando Calrissian",
        "Qi'ra",
        "Tobias Beckett",
        "Val",
        "Rio Durant",
        "L3-37",
        "Dryden Vos",
        "Enfys Nest",
        "Darth Maul",
    ],
    # Trilogía de Secuelas (Episodios VII, VIII, IX)
    "the-force-awakens": [
        "Rey",
        "Kylo Ren",
        "Finn",
        "Poe Dameron",
        "BB-8",
        "Supreme Leader Snoke",
        "Captain Phasma",
        "General Hux",
        "Maz Kanata",
    ],
    "the-last-jedi": [
        "Rose Tico",
        "Amilyn Holdo",
        "Luke Skywalker",
        "Princess Leia Organa",
        "Kylo Ren",
        "Rey",
        "Finn",
        "Poe Dameron",
    ],
    "the-rise-of-skywalker": [
        "Zorii Bliss",
        "Babu Frik",
        "Jannah",
        "D-O",
        "Emperor Palpatine",
        "Rey",
        "Kylo Ren",
        "General Pryde",
    ],
    # Precuelas clave no indexadas originalmente
    "prequels-expansion": [
        "Count Dooku",
        "General Grievous",
        "Padme Amidala",
        "Clone Commander Cody",
        "Zam Wesell",
        "Dexter Jettster",
        "Watto",
        "Sebulba",
    ],
    # Expansión A New Hope (Episodio IV) - Para completar los 33+ personajes de cine
    "a-new-hope-expansion": [
        "Jan Dodonna",
        "Admiral Motti",
        "General Tagge",
        "Ponda Baba",
        "Doctor Cornelius Evazan",
        "Wuher",
        "Garindan",
        "Momaw Nadon",
        "Garven Dreis",
        "BoShek",
    ],
    # Expansión El Imperio Contraataca (Episodio V)
    "the-empire-strikes-back-expansion": [
        "General Veers",
        "Admiral Piett",
        "Captain Needa",
        "Lobot",
        "Dengar",
        "Bossk",
        "Zuckuss",
        "4-LOM",
        "IG-88",
        "Dak Ralter",
    ],
    # Expansión El Retorno del Jedi (Episodio VI)
    "return-of-the-jedi-expansion": [
        "Admiral Ackbar",
        "Nien Nunb",
        "Wicket W. Warrick",
        "Max Rebo",
        "Oola",
        "Malakili",
        "Moff Jerjerrod",
    ],
    # Consejo Jedi y Precuelas
    "prequels-jedi-council": [
        "Plo Koon",
        "Kit Fisto",
        "Aayla Secura",
        "Ki-Adi-Mundi",
        "Shaak Ti",
        "Saesee Tiin",
        "Luminara Unduli",
        "Boss Nass",
        "Nute Gunray",
        "Mas Amedda",
    ],
    # Expansión Rogue One
    "rogue-one-expansion": [
        "Bistan",
        "Pao",
        "Lyra Erso",
        "Edrio Two Tubes",
        "Benthic Two Tubes",
        "General Draven",
        "Moroff",
    ],
    # Expansión Solo: A Star Wars Story
    "solo-expansion": [
        "Lady Proxima",
        "Quay Tolsite",
        "Rebolt",
    ],
    # Expansión Andor
    "andor-expansion": [
        "Karis Nemik",
        "Arvel Skeen",
        "Tay Kolma",
        "Major Partagaz",
        "Eedy Karn",
        "Lonni Jung",
        "Salman Paak",
    ],
    # Expansión Obi-Wan Kenobi
    "obi-wan-expansion": [
        "Ned-B",
        "Freck",
        "Kawlan Roken",
    ],
    # Expansión The Acolyte
    "acolyte-expansion": [
        "Sol",
        "Indara",
        "Kelnacca",
        "Torbin",
        "Mog Adana",
        "Senator Rayencourt",
    ],
    # Expansión Skeleton Crew
    "skeleton-crew-expansion": [
        "Gunter",
    ],
    # Expansión The Mandalorian & The Book of Boba Fett
    "mandoverse-expansion": [
        "Toro Calican",
        "Xi An",
        "Burg",
        "Valin Hess",
        "Krrsantan",
        "Mayor Mok Shaiz",
    ],
    # Expansión Trilogía de Secuelas & Caballeros de Ren
    "sequels-expansion": [
        "Unkar Plutt",
        "Bala-Tik",
        "Tasu Leech",
        "Sidon Ithano",
        "Snap Wexley",
        "Jess Pava",
        "Paige Tico",
        "DJ",
        "Vicrul",
        "Cardo",
        "Ushar",
        "Trudgen",
        "Kuruk",
        "Ap-lek",
    ],
    # Expansión Precuelas (Episodios I, II, III)
    "prequels-expansion-2": [
        "Captain Panaka",
        "Rune Haako",
        "Ric Olie",
        "Sabe",
        "Gasgano",
        "Ben Quadinaros",
        "Tarfful",
        "Tion Medon",
        "Sly Moore",
    ],
}

# Producciones animadas con personajes curados listos para procesar
ANIMATED_SERIES_CHARACTERS: dict[str, list[str]] = {
    "the-clone-wars": [
        "Clone Captain Rex",
        "Clone Commander Wolffe",
        "Gregor",
        "Clone Commander Fox",
        "Arc Trooper Fives",
        "Echo",
        "Clone 99",
        "Jesse",
        "Waxer",
        "Boil",
        "Clone Commander Thorn",
        "Clone Commander Stone",
        "Clone Commander Doom",
        "Clone Commander Ponds",
        "Asajj Ventress",
        "Savage Opress",
        "Mother Talzin",
        "Pre Vizsla",
        "Admiral Trench",
        "General Pong Krell",
        "Aurra Sing",
        "Sugi",
        "Embo",
        "Rush Clovis",
        "Duchess Satine Kryze",
        "Hondo Ohnaka",
        "Cham Syndulla",
        "Steela Gerrera",
        "Quinlan Vos",
        "Tera Sinube",
        "Ahsoka Tano",
    ],
    "the-bad-batch": [
        "Hunter",
        "Wrecker",
        "Tech",
        "Crosshair",
        "Echo",
        "Omega",
        "Cid",
        "Phee Genoa",
        "Vice Admiral Rampart",
        "Dr Royce Hemlock",
        "Clone Captain Howzer",
        "Clone Commander Scorch",
        "Clone Commander Mayday",
        "Clone Captain Grey",
        "Clone X Trooper",
        "Gungi",
        "Riyo Chuchi",
        "Shep Hazard",
        "Mox",
        "Stak",
    ],
    "star-wars-rebels": [
        "Kanan Jarrus",
        "Zeb Orrelios",
        "Alexsandr Kallus",
        "Seventh Sister Inquisitor",
        "Eighth Brother Inquisitor",
        "Governor Pryce",
        "Valen Rudor",
        "Fenn Rau",
        "Gar Saxon",
        "Tristan Wren",
        "Ursa Wren",
        "Alrich Wren",
        "AP-5",
        "Ketsu Onyo",
        "Mart Mattin",
        "Bendu",
        "Azmorigan",
        "Morad Sumar",
        "Quarrie",
        "General Kalani",
        "Chava",
        "Chopper",
        "Ezra Bridger",
        "Sabine Wren",
        "Hera Syndulla",
        "Ryder Azadi",
        "Jai Kell",
    ],
    "star-wars-resistance": [
        "Kazuda Kaz Xiono",
        "Jarek Yeager",
        "Torra Doza",
        "Tam Ryvora",
        "Neeku Vozo",
        "Commander Pyre",
        "Captain Doza",
        "Hype Fazon",
        "Freya Fenris",
        "Bo Keevil",
        "Griff Halloran",
        "CB-23",
        "Synara San",
        "Major Vonreg",
        "Agent Tierny",
        "Kel",
        "Eila",
        "Flix",
        "Orka",
        "Kragan Gorr",
    ],
}

# Slugs de personajes que son soldados clones
CLONE_SLUGS: set[str] = {
    "clone-captain-rex", "captain-rex", "rex",
    "clone-commander-wolffe", "commander-wolffe", "wolffe",
    "gregor", "commander-gregor", "clone-captain-gregor",
    "clone-commander-fox", "commander-fox",
    "arc-trooper-fives", "fives",
    "echo", "arc-trooper-echo",
    "clone-99", "99",
    "jesse", "clone-trooper-jesse",
    "waxer", "boil",
    "clone-commander-thorn",
    "clone-commander-stone",
    "clone-commander-doom",
    "clone-commander-ponds",
    "clone-commander-cody", "commander-cody",
    "clone-commander-gree", "commander-gree",
    "clone-commander-bly", "commander-bly",
    "clone-commander-bacara", "commander-bacara",
    "clone-commander-neyo", "commander-neyo",
    "hunter", "wrecker", "tech", "crosshair", "omega",
    "mox", "stak",
    "clone-captain-howzer", "clone-commander-scorch", "clone-captain-grey",
    "clone-commander-mayday", "clone-x-trooper",
}


def is_clone_character(slug: str, name: str = "") -> bool:
    """Identifica si un personaje es un soldado clon."""
    clean_slug = slug.strip().lower()
    clean_name = name.strip().lower()
    if clean_slug in CLONE_SLUGS:
        return True
    if clean_slug.startswith("clone-") or "-clone-" in clean_slug:
        return True
    if "clone trooper" in clean_name or "arc trooper" in clean_name or "clone commander" in clean_name:
        return True
    return False


# Producciones ANIMADAS expresamente excluidas para evitar descargar ilustraciones/dibujos
ANIMATED_PRODUCTIONS: set[str] = {
    "the-clone-wars",
    "star-wars-rebels",
    "the-bad-batch",
    "star-wars-resistance",
    "star-wars-visions",
    "tales-of-the-jedi",
    "tales-of-the-empire",
    "forces-of-destiny",
    "young-jedi-adventures",
    "star-wars-droids",
    "star-wars-ewoks",
}


def is_animated(slug: str) -> bool:
    """Retorna True si el slug corresponde a una producción animada."""
    clean_slug = slug.strip().lower().replace("_", "-")
    return clean_slug in ANIMATED_PRODUCTIONS


def is_live_action(slug: str) -> bool:
    """Retorna True si el slug corresponde a una producción Live-Action registrada."""
    clean_slug = slug.strip().lower().replace("_", "-")
    return clean_slug in LIVE_ACTION_PRODUCTIONS


def get_production_characters(slug: str) -> list[str]:
    """
    Obtiene la lista de nombres de personajes para una producción live-action o animada curada.
    """
    clean_slug = slug.strip().lower().replace("_", "-")
    if clean_slug in LIVE_ACTION_PRODUCTIONS:
        return LIVE_ACTION_PRODUCTIONS[clean_slug]
    if clean_slug in ANIMATED_SERIES_CHARACTERS:
        return ANIMATED_SERIES_CHARACTERS[clean_slug]
    if is_animated(clean_slug):
        raise ValueError(
            f"La producción animada '{slug}' aún no tiene una lista de personajes curada."
        )
    return []


def list_live_action_productions() -> list[str]:
    """Retorna la lista de slugs de producciones Live-Action disponibles."""
    return list(LIVE_ACTION_PRODUCTIONS.keys())


def list_animated_productions() -> list[str]:
    """Retorna la lista de producciones animadas registradas."""
    return sorted(list(ANIMATED_PRODUCTIONS))


def list_available_animated_series() -> list[str]:
    """Retorna la lista de series animadas con personajes curados listos."""
    return list(ANIMATED_SERIES_CHARACTERS.keys())


# Compatibilidad retroactiva para imports existentes
SERIES_CHARACTERS = {**LIVE_ACTION_PRODUCTIONS, **ANIMATED_SERIES_CHARACTERS}
get_series_characters = get_production_characters
list_available_series = list_live_action_productions
