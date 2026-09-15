from src.core.entities.character import CharacterEntity, PhysicalTraits
from src.application.services.deduplication_service import deduplicate_and_merge_characters


def test_deduplicate_merges_appearances_and_affiliations():
    char1 = CharacterEntity(
        id=1,
        slug="luke-skywalker",
        name="Luke Skywalker",
        appearances=["A New Hope", "The Empire Strikes Back"],
        affiliations=["Rebel Alliance"],
        description="A short bio of Luke.",
    )
    char2 = CharacterEntity(
        id=2,
        slug="luke-skywalker",
        name="Luke Skywalker",
        appearances=["Return of the Jedi", "The Mandalorian"],
        affiliations=["Jedi Order", "Rebel Alliance"],
        description="A much more detailed and longer biography of Luke Skywalker the Jedi Knight.",
        avatar_url="https://starwars.com/luke.jpg",
    )

    merged = deduplicate_and_merge_characters([char1, char2])

    assert len(merged) == 1
    result = merged[0]
    assert result.id == 1
    assert result.slug == "luke-skywalker"
    # Merged appearances
    assert set(result.appearances) == {
        "A New Hope",
        "The Empire Strikes Back",
        "Return of the Jedi",
        "The Mandalorian",
    }
    # Merged affiliations
    assert set(result.affiliations) == {"Rebel Alliance", "Jedi Order"}
    # Better description kept
    assert result.description == "A much more detailed and longer biography of Luke Skywalker the Jedi Knight."
    # Avatar retained
    assert result.avatar_url == "https://starwars.com/luke.jpg"


def test_deduplicate_preserves_unique_characters():
    char1 = CharacterEntity(id=1, slug="luke-skywalker", name="Luke Skywalker")
    char2 = CharacterEntity(id=2, slug="leia-organa", name="Leia Organa")

    merged = deduplicate_and_merge_characters([char1, char2])

    assert len(merged) == 2
    assert [c.id for c in merged] == [1, 2]
    assert [c.slug for c in merged] == ["luke-skywalker", "leia-organa"]
