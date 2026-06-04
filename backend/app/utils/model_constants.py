from enum import Enum

class AIModel(str, Enum):

    DE_FLASH = "deepseek/deepseek-v4-flash"
    MIMO = "xiaomi/mimo-v2.5"
    DE_PRO = "deepseek/deepseek-v4-pro"

FALLBACK_MODELS = [AIModel.MIMO.value, AIModel.DE_PRO.value]
MODEL = AIModel.DE_FLASH.value

