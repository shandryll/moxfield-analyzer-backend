class CardTypeHelper:
    @staticmethod
    def get_front_face_type_line(card: dict) -> str:
        faces = card.get("card_faces")
        if isinstance(faces, list) and faces:
            front = faces[0]
            if isinstance(front, dict):
                return str(front.get("type_line", ""))
        return str(card.get("type_line", ""))

    @staticmethod
    def is_creature_or_commander_planeswalker(type_line: str, is_commander: bool) -> bool:
        lower = type_line.lower()
        is_creature = "creature" in lower
        is_legendary_pw = "legendary" in lower and "planeswalker" in lower
        if is_commander:
            return is_creature or is_legendary_pw
        return is_creature

    @staticmethod
    def count_creatures(board: dict, is_commander: bool) -> int:
        total = 0
        for slot in board.values():
            if not isinstance(slot, dict):
                continue
            card = slot.get("card", {})
            if not isinstance(card, dict):
                continue
            quantity = slot.get("quantity", 1)
            if not isinstance(quantity, (int, float)):
                quantity = 1
            type_line = CardTypeHelper.get_front_face_type_line(card)
            if CardTypeHelper.is_creature_or_commander_planeswalker(type_line, is_commander):
                total += int(quantity)
        return total
