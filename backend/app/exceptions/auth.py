from app.exceptions.base import AppException


class AuthenticationError(AppException):

    status_code = 401
    detail = "Authentication failed"


class InvalidTokenError(AuthenticationError):

    detail = "Invalid authentication token"


class ExpiredTokenError(AuthenticationError):

    detail = "Authentication token expired"


class UserAlreadyExistsError(AppException):

    status_code = 409
    detail = "User already exists"


class SignupError(AppException):

    status_code = 400
    detail = "Signup failed"


class EmailNotVerifiedError(AppException):

    status_code = 403
    detail = "Please verify your email before logging in"


class InvalidCredentialsError(AppException):

    status_code = 400
    detail = "Invalid email or password"


class PasswordResetError(AppException):

    status_code = 400
    detail = "Password reset failed. The link may have expired."
