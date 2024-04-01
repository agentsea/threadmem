<!-- PROJECT LOGO -->
<br />
<p align="center">
  <!-- <a href="https://github.com/agentsea/skillpacks">
    <img src="https://project-logo.png" alt="Logo" width="80">
  </a> -->

  <h1 align="center">threadmem</h1>

  <p align="center">
    Chat thread memory for AI agents
    <br />
    <a href="https://github.com/agentsea/threadmem"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/agentsea/threadmem">View Demo</a>
    ·
    <a href="https://github.com/agentsea/threadmem/issues">Report Bug</a>
    ·
    <a href="https://github.com/agentsea/threadmem/issues">Request Feature</a>
  </p>
  <br>
</p>

Threadmem enables robust chat experiences with AI agents. It offers a Python backend for managing thread state as well as a React chat interface.

## Backend

### Installation

```
pip install threadmem
```

### Usage

#### Role Threads

Create a role based thread and store in a local sqlite database

```python
from threadmem import RoleThread

thread = RoleThread()
thread.post("user", "Hello, Thread!")

# output in openai chat schema format
print(thread.to_oai())
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
