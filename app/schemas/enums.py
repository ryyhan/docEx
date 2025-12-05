from enum import Enum

class VlmMode(str, Enum):
    NONE = "none"
    LOCAL = "local"
    API = "api"
