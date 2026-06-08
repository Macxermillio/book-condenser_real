from app.exceptions.base import AppException


class RateLimitError(AppException):

    status_code = 429
    detail = (
        "You have exceeded the rate limit for uploading files. "
        "If you have uploaded a file within the last 15 minutes, wait before uploading again."
    )


class FileUploadError(AppException):

    status_code = 400
    detail = "File upload failed"


class FileDownloadError(AppException):

    status_code = 400
    detail = "File download failed"


class TextExtractionError(AppException):

    status_code = 400
    detail = "Text extraction failed"


class LLMProcessingError(AppException):

    status_code = 500
    detail = "LLM processing failed"
