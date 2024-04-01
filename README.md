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

Role based threads are useful for managing openai-style chat schemas.

```python
from threadmem import RoleThread

# Create a thread storing it in a local sqlite db
thread = RoleThread(owner_id="john@jacobs.ai")

# Post messages
thread.post("user", "Hello, Thread!")
thread.post("assistant", "How can I help?")
thread.post("user", "Whats this image?", images=["data:image/jpeg;base64,..."])

# output in openai chat schema format
print(thread.to_oai())

# Find a thread
threads = RoleThread.find(owner_id="john@jacobs.ai")

# Delete a thread
threads[0].delete()
```

##### Supported Backends

- Sqlite
- Postgresql

## Develop

To test

```sh
make test
```

To publish

```sh
make publish
```
