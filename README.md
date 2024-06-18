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
    <a href="https://docs.hub.agentsea.ai/threadmem/intro"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://youtu.be/exoOUUwFRB8">View Demo</a>
    ·
    <a href="https://github.com/agentsea/threadmem/issues">Report Bug</a>
    ·
    <a href="https://github.com/agentsea/threadmem/issues">Request Feature</a>
  </p>
  <br>
</p>

ThreadMem is a simple tool that helps manage chat conversations with language models.

## Installation

```
pip install threadmem
```

## Usage

### Role Threads

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

Add images of any variety to the thread. We support base64, filepath, PIL, and URL:

```python
from PIL import Image

img1 = Image.open("img1.png")

thread.post(
  role="user",
  msg="Whats this image?",
  images=["data:image/jpeg;base64,...", "./img1.png", img1, "https://shorturl.at/rVyAS"]
)
```

## Integrations

Threadmem is integrated into:

- [MLLM](https://github.com/agentsea/mllm) - A prompt management, routing, and schema validation library for multimodal LLMs.
- [Taskara](https://github.com/agentsea/taskara) - A task management library for AI agents.
- [Skillpacks](https://github.com/agentsea/skillpacks) - A library to fine tune AI agents on tasks.
- [SurfKit](https://github.com/agentsea/surfkit) - A platform for AI agents.

## Community

Come join us on [Discord](https://discord.gg/hhaq7XYPS6).

## Backends

Thread and prompt storage can be backed by:

- Sqlite
- Postgresql

Sqlite will be used by default. To use postgres simply configure the env vars:

```sh
DB_TYPE=postgres
DB_NAME=threads
DB_HOST=localhost
DB_USER=postgres
DB_PASS=abc123
```

Image storage by default will utilize the db, to configure bucket storage using GCS:

- Create a bucket with fine grained permissions
- Create a GCP service account JSON with permissions to write to the bucket

```sh
export THREAD_STORAGE_SA_JSON='{
  "type": "service_account",
  ...
}'
export THREAD_STORAGE_BUCKET=my-bucket
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
