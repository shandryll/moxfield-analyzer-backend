import asyncio
from loguru import logger
from src.domain.value_objects.deck_url import DeckUrl
from src.domain.services.kindred_wars_calculator import KindredWarsCalculator
from src.domain.services.mana_curve_calculator import ManaCurveCalculator
from src.domain.services.card_type_helper import CardTypeHelper
from src.infrastructure.repositories.moxfield_deck_repository import MoxfieldDeckRepository
from src.infrastructure.repositories.scryfall_card_resolver import ScryfallCardResolver
from src.infrastructure.repositories.card_mapper import CardMapper
from src.infrastructure.repositories.commander_spellbook_repository import CommanderSpellbookRepository
from src.shared.models import Card, ComboCardInfo, DeckDetails


class ValidateDeckUseCase:
    def __init__(
        self,
        deck_repo: MoxfieldDeckRepository | None = None,
        oracle_resolver: ScryfallCardResolver | None = None,
        card_mapper: CardMapper | None = None,
        kindred_calc: KindredWarsCalculator | None = None,
        mana_curve_calc: ManaCurveCalculator | None = None,
        combos_repo: CommanderSpellbookRepository | None = None,
    ) -> None:
        self._deck_repo = deck_repo or MoxfieldDeckRepository()
        self._oracle_resolver = oracle_resolver or ScryfallCardResolver()
        self._card_mapper = card_mapper or CardMapper()
        self._kindred_calc = kindred_calc or KindredWarsCalculator()
        self._mana_curve_calc = mana_curve_calc or ManaCurveCalculator()
        self._combos_repo = combos_repo or CommanderSpellbookRepository()

    async def execute(self, url: str, kindred: str) -> DeckDetails:
        deck_url = DeckUrl(url)
        raw = await self._deck_repo.get_by_id(deck_url.value)

        mainboard = raw.get("mainboard", {}) or {}
        commanders = raw.get("commanders", {}) or {}
        companions = raw.get("companions", {}) or {}

        all_sf_ids = (
            self._card_mapper.extract_scryfall_ids(mainboard)
            + self._card_mapper.extract_scryfall_ids(commanders)
            + self._card_mapper.extract_scryfall_ids(companions)
        )

        oracle_id_map = await self._oracle_resolver.resolve(all_sf_ids)

        cards = self._card_mapper.board_to_cards(mainboard, oracle_id_map)
        commander_cards = self._card_mapper.board_to_cards(commanders, oracle_id_map)
        companion_cards = self._card_mapper.board_to_cards(companions, oracle_id_map)
        all_cards = cards + commander_cards + companion_cards

        creatures = CardTypeHelper.count_creatures(mainboard, False)
        commander_creatures = CardTypeHelper.count_creatures(commanders, True)
        companion_creatures = CardTypeHelper.count_creatures(companions, False)
        creatures_including_cmdrs = creatures + commander_creatures + companion_creatures

        total_cards = sum(c.quantity for c in all_cards)
        non_creatures = total_cards - creatures_including_cmdrs

        kindred_wars, mana_curve, find_my_combos = await asyncio.gather(
            asyncio.to_thread(
                self._kindred_calc.calculate_kindred_wars,
                all_cards, mainboard, commanders, companions,
                kindred, creatures_including_cmdrs,
            ),
            asyncio.to_thread(
                self._mana_curve_calc.build_mana_curve,
                mainboard, commanders,
            ),
            self._safe_fetch_combos(cards, commander_cards),
        )

        return DeckDetails(
            id=str(raw.get("id", "")),
            name=str(raw.get("name", "")),
            description=str(raw.get("description", "")),
            public_url=str(raw.get("public_url", "")),
            total_cards=total_cards,
            creatures=creatures,
            non_creatures=non_creatures,
            commander_creatures=commander_creatures,
            companion_creatures=companion_creatures,
            creatures_including_commanders=creatures_including_cmdrs,
            mana_curve=mana_curve,
            kindred_wars=kindred_wars,
            find_my_combos=find_my_combos,
            cards=cards,
            commanders=commander_cards,
            companions=companion_cards,
            created_at=str(raw.get("created_at", "")),
            updated_at=str(raw.get("updated_at", "")),
        )

    async def _safe_fetch_combos(
        self,
        cards: list[Card],
        commander_cards: list[Card],
    ) -> list[ComboCardInfo]:
        try:
            return await self._combos_repo.find_for_cards(cards, commander_cards)
        except Exception as e:
            logger.error("Failed to fetch combos", error=str(e), exception_type=type(e).__name__)
            return []
