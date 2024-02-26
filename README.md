<!-- PROJECT LOGO -->
<br />
<p align="center">
  <!-- <a href="https://github.com/agentsea/skillpacks">
    <img src="https://project-logo.png" alt="Logo" width="80">
  </a> -->

  <h1 align="center">deepthread</h1>

  <p align="center">
    Rich chat threads for AI agents
    <br />
    <a href="https://github.com/agentsea/deepthread"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/agentsea/deepthread">View Demo</a>
    ·
    <a href="https://github.com/agentsea/deepthread/issues">Report Bug</a>
    ·
    <a href="https://github.com/agentsea/deepthread/issues">Request Feature</a>
  </p>
  <br>
</p>

Deepthread enables robust chat experiences with AI agents. It offers a Python backend for managing thread state as well as a React chat interface.

We support [Agentscript](https://github.com/agentsea/agentscript) for beautiful UI experiences.

## Backend

### Installation

```
pip install deepthread
```

### Usage

#### Role Threads

Create a role based thread

```python
from deepthread import Thread

thread = Thread()
thread.post("user", "Hello, Thread!")

# output in openai chat schema format
print(thread.to_oai())
```

## Frontend

### Installation

```
npm i @agentsea/deepthread
```

## Develop

To test

```sh
make test
```

To publish

```sh
make publish
```
