# Domain-specific exceptions
class UserAlreadyExists(Exception):
    pass

class UserNotFound(Exception):
    pass

class InvalidCredentials(Exception):
    pass

class NotPermitted(Exception):
    pass

class TokenError(Exception):
    pass

class DatabaseError(Exception):
    pass

class ProjectNotFound(Exception):
    pass

class ProjectExists(Exception):
    pass