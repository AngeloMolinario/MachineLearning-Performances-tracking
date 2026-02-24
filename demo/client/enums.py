import enum

class SplitEnum(str, enum.Enum):
    train = "train"
    validation = "validation"

class StatusEnum(str, enum.Enum):
    running = 'running'
    completed = 'completed'
    failed = 'failed'

class MetricEnum(str, enum.Enum):
    accuracy = 'accuracy'
    f1_score = 'f1-score'
    recall   = 'recall'
    precision = 'precision'
    balanced_accuracy = 'balanced accuracy'
    mse = 'mse'
    mae = 'mae'