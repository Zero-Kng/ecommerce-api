class DomainError(Exception):
    """Falha de regra de negócio, independente de protocolo de transporte."""

    code = "DOMAIN_ERROR"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class ConflictError(DomainError):
    code = "CONFLICT"


class CategoryInUseError(ConflictError):
    code = "CATEGORY_IN_USE"


class DuplicateResourceError(ConflictError):
    code = "DUPLICATE_RESOURCE"


class PermissionDeniedError(DomainError):
    code = "PERMISSION_DENIED"
