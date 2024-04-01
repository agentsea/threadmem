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

Threadmem is a simple tool that helps manage chat conversations with language models.

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
thread = RoleThread(owner_id="dolores@agentsea.ai")

# Post messages
thread.post("user", "Hello, Thread!")
thread.post("assistant", "How can I help?")
thread.post("user", "Whats this image?", images=["data:image/jpeg;base64,..."])

# Output in openai chat schema format
print(thread.to_oai())

# Find a thread
threads = RoleThread.find(owner_id="dolores@agentsea.ai")

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
