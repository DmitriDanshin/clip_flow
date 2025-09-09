from enum import Enum


class SettingType(Enum):
    INTEGER = "integer"
    FLOAT = "float" 
    BOOLEAN = "boolean"
    STRING = "string"
    SLIDER = "slider"