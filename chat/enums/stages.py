from enum import Enum


class Stages(str, Enum):
    TEST: str = 'TEST'
    PROD: str = 'PROD'
