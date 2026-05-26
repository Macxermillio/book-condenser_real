from app.exceptions.base import AppException

MAX_INPUT_CHARS = 3_500_000


class InputTooLargeError(AppException):

    status_code = 400

    def __init__(self, length: int):
        super().__init__(
            detail=f"Input exceeds maximum allowed length: {MAX_INPUT_CHARS} characters",
            log_message=(
                f"Input length {length:,} exceeds "
                f"{MAX_INPUT_CHARS:,} characters"
            ),
        )
