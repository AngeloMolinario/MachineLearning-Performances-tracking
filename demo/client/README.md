# TrainTrack Client

Lightweight Python client to log experiments to your [TrainTrack](../README.md) server during training.

## Installation

Copy the `client/` folder into your ML project:

```
your_project/
├── client/
│   ├── traintrack.py
│   └── enums.py
├── train.py
└── ...
```

Install the only dependency:

```bash
pip install requests
```

## Quick Start

```python
from client.traintrack import TrainTrackClient
from client.enums import SplitEnum, MetricEnum

# Connect to the TrainTrack server
tt = TrainTrackClient("http://localhost:8000")

# 1. Register your model (model_id is saved internally)
tt.create_model("ResNet50", "Image Classification")

# 2. Start a training run (run_id is saved internally)
tt.create_run(hyperparameters={"lr": 0.001, "batch_size": 32, "epochs": 50})

# 3. Log loss and metrics inside your training loop
for epoch in range(50):
    train_loss = train(...)
    val_loss = validate(...)
    accuracy = evaluate(...)

    # Log loss
    tt.log_loss(step=epoch, split=SplitEnum.train, value=train_loss)
    tt.log_loss(step=epoch, split=SplitEnum.validation, value=val_loss)

    # Log metrics
    tt.log_metric(step=epoch, split=SplitEnum.validation, metric_name=MetricEnum.accuracy, value=accuracy)

# 4. Mark the run as completed
tt.complete_run()
```

## Available Enums

### `SplitEnum`
| Value | Usage |
|---|---|
| `SplitEnum.train` | Training split |
| `SplitEnum.validation` | Validation split |

### `MetricEnum`
| Value | Usage |
|---|---|
| `MetricEnum.accuracy` | Accuracy |
| `MetricEnum.f1_score` | F1-Score |
| `MetricEnum.recall` | Recall |
| `MetricEnum.precision` | Precision |
| `MetricEnum.balanced_accuracy` | Balanced Accuracy |
| `MetricEnum.mse` | Mean Squared Error |
| `MetricEnum.mae` | Mean Absolute Error |

## API Reference

| Method | Description |
|---|---|
| `create_model(name, project_name)` | Register a model (saves `model_id`) |
| `create_run(hyperparameters)` | Start a run (saves `run_id`) |
| `log_loss(step, split, value)` | Log a loss value |
| `log_losses(losses)` | Log a batch of loss values |
| `log_metric(step, split, metric_name, value)` | Log a metric value |
| `log_metrics(metrics)` | Log a batch of metric values |
| `complete_run()` | Mark current run as completed |
| `fail_run()` | Mark current run as failed |
| `get_models()` | List all models |
| `get_runs()` | List runs for the current model |
| `get_losses(split)` | Get losses for the current run |
| `get_metrics(split, metric_name)` | Get metrics for the current run |

> **Note:** `model_id` and `run_id` are stored internally after `create_model()` and `create_run()`. You don't need to pass them manually, but all methods accept optional overrides if needed.
