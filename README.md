# deepthread

Rich threads for AI agents

Deepthread provides a chat abstraction for AI agents with a Python abstraction on the backend and a React abstraction on the frontend. We support [Agentscript](https://github.com/agentsea/agentscript) for beautiful UI experiences.

## Backend

### Installation

```
pip install deepthread
```

### Usage

```python
from deepthread import Thread

thread = Thread()
thread.post("user123", "Hello, Thread!")

print(thread.messages())
```

## Frontend

### Installation

```
npm i @agentsea/deepthread
```
