import enum


class WasteCategoryEnum(str, enum.Enum):
    ORGANIC = "ORGANIC"
    FOOD_WASTE = "FOOD_WASTE"
    PLASTIC = "PLASTIC"
    PAPER = "PAPER"
    GLASS = "GLASS"
    METAL = "METAL"
    NOT_WASTE = "NOT_WASTE"


class ActionTypeEnum(str, enum.Enum):
    PROCESS_MYSELF = "PROCESS_MYSELF"
    REUSE = "REUSE"
    RECYCLE = "RECYCLE"
    ALLOCATE = "ALLOCATE"


class DifficultyEnum(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
