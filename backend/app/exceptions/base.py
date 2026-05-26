class AppException(Exception):

    status_code = 500
    detail = "Application error"

    def __init__(
        self,
        detail: str = None,
        log_message: str = None,
    ):
        self.detail = detail or self.__class__.detail
        self.log_message = log_message or self.detail
        super().__init__(self.detail)
