# keyman

Centralized API key orchestration system for managing rate-limited API keys across distributed Celery workers.

## Overview

keyman coordinates API key distribution and rate limit tracking between a central orchestrator and multiple worker processes via Redis pub/sub.

**Key features:**
- Round-robin key distribution (random selection)
- Automatic rate limit tracking and key refresh
- Support for multiple platforms (GitHub REST/GraphQL/Search, GitLab)

## Architecture

```
┌──────────────┐
│ Orchestrator │ ← Single process managing all keys
└──────┬───────┘
       │ Redis pub/sub
       ↓
┌──────────────┐
│ KeyClient    │ ← One per worker per platform
└──────────────┘
```

### Components

**KeyOrchestrator** (`Orchestrator.py`)
- Central key manager (single process)
- Maintains fresh, expired, and invalid key pools
- Listens on Redis channels for key requests

**KeyClient** (`KeyClient.py`)
- Worker-side interface for requesting keys
- NOT thread-safe (uses process ID for channels)
- Blocks until keys are available

**KeyPublisher** (`KeyClient.py`)
- Admin interface for publishing/unpublishing keys
- Used during Augur startup to load keys from database

## Usage

### Request a key (worker)

```python
from keyman.KeyClient import KeyClient

# Initialize once per process
client = KeyClient("github_rest", logger)

# Request a key (blocks if none available)
key = client.request()

# Use key for API call...

# Expire key when rate limited
epoch_reset = int(response.headers["X-RateLimit-Reset"])
new_key = client.expire(key, epoch_reset)

# Invalidate key on 401
new_key = client.invalidate(key)
```

### Publish keys (startup)

```python
from keyman.KeyClient import KeyPublisher

pub = KeyPublisher()

# Add key to orchestrator
pub.publish("ghp_abc123", "github_rest")

# Check health
if pub.wait(timeout_seconds=30, republish=True):
    print("Orchestrator ready")
```

## Supported Platforms

| Platform | Use Case | Rate Limit |
|----------|----------|------------|
| `github_rest` | GitHub REST API v3 | 5000 req/hour |
| `github_graphql` | GitHub GraphQL API v4 | 5000 points/hour |
| `github_search` | GitHub Search API | 30 req/min |
| `gitlab_rest` | GitLab REST API | Varies |

**Note**: Same GitHub token is published to all three `github_*` platforms because GitHub enforces separate rate limits for each API type.

## Key States

**Fresh** → Available for assignment to workers
**Expired** → Rate limited, will refresh when timeout passes
**Invalid** → Permanently bad (401), never refreshed

## Redis Channels

**`augur-oauth-announce`** - Admin operations (PUBLISH, UNPUBLISH, SHUTDOWN)
**`worker-oath-request`** - Worker operations (NEW, EXPIRE, INVALIDATE)

Responses sent to `{channel}-{process_id}`

## Starting the Orchestrator

The orchestrator is started automatically by Augur backend:

```python
# In augur/application/cli/backend.py
orchestrator = subprocess.Popen("python keyman/Orchestrator.py".split())
```

For manual testing:
```bash
python keyman/Orchestrator.py
```

## Adding Keys

```sql
INSERT INTO augur_operations.worker_oauth
(name, consumer_key, consumer_secret, access_token, access_token_secret, platform)
VALUES
('My GitHub Key', 'not_used', 'not_used', 'ghp_YOURTOKEN', 'not_used', 'github_rest');
```

Keys are loaded on Augur startup and published to orchestrator.

## Troubleshooting

**Workers hang indefinitely**
- Check orchestrator is running: `ps aux | grep Orchestrator.py`
- Check Redis connectivity
- Verify keys exist: `pub.list_keys("github_rest")`

**All keys expired**
- Check rate limit reset times in GitHub response headers
- Add more keys to database
- Wait for keys to refresh automatically

**Keys not loading on startup**
- Verify `worker_oauth` table has keys
- Check `GithubApiKeyHandler` logs for validation errors
- Ensure Redis is accessible

## Files

| File | Purpose |
|------|---------|
| `Orchestrator.py` | Central key manager |
| `KeyClient.py` | Worker + admin interfaces |
| `KeyOrchestrationAPI.py` | Protocol specification |

## Limitations

- NOT thread-safe (uses process IDs)
- No persistence (state lost on orchestrator restart)
- Blocks indefinitely if no keys available
- Single orchestrator (no clustering/HA)
