from typing import NewType

from hack.core.models import User, LoginSession

AuthorizedUser = NewType("AuthorizedUser", User)
CurrentLoginSession = NewType("CurrentLoginSession", LoginSession)
