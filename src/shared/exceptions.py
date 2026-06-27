class NotFoundMoxfieldError(Exception):
    pass


class MoxfieldError(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(message)


class CommanderSpellbookError(Exception):
    pass


class CommanderSpellbookTimeoutError(CommanderSpellbookError):
    pass


class CommanderSpellbookRateLimitError(CommanderSpellbookError):
    pass


class CommanderSpellbookApiError(CommanderSpellbookError):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(message)
