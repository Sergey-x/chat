from enum import Enum


class Stages(str, Enum):
    TEST: str = 'TEST'
    DEV: str = 'DEV'
    PROD: str = 'PROD'
