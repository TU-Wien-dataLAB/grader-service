# LTI Grade Synchronization

The Grader Service includes an **LTI 1.3 Advantage** grade sync plugin that can push grades to one or more LTI-compatible platforms (e.g. Moodle, Canvas).

## Overview

When a grade sync is triggered — either manually via the REST API or automatically after feedback generation — the plugin:

1. Selects which configured LTI platforms to sync to.
2. For each platform, requests a **bearer token** via OAuth 2.0 client credentials with a signed JWT assertion.
3. Resolves the **NRPS membership** and **AGS lineitem** URLs for the lecture / assignment.
4. Fetches course members from the platform and matches them to grader submissions.
5. Creates or finds a lineitem for the assignment.
6. Pushes grades to the platform.

Errors on one platform do not prevent syncing to the remaining platforms.

## Enabling the Plugin

```python
# grader_service_config.py
c.LTISyncGrades.enabled = True

# Optional: automatically sync grades when feedback is generated
c.LTISyncGrades.sync_on_feedback = True
```

`enabled` and `sync_on_feedback` accept either a `bool` value or a callable with the signature:
```python
def check(lecture: dict, assignment: dict, submissions: list[dict]) -> bool
```

## Configuring LTI Systems

Each LTI platform is described as a dictionary in the `systems` list:

```python
c.LTISyncGrades.systems = [
    {
        "name": "MyMoodle",                            # unique identifier (required)
        "url_pattern": "https://moodle.university.edu",   # base URL pattern (required)
        "client_id": "my-client-id",                      # OAuth2 client ID (required)
        "token_url": "https://moodle.university.edu/mod/lti/token.php",  # token endpoint (required)
        "private_key_path": "/secrets/lti/moodle_private_key.pem", # path to PEM-encoded RSA private key for JWT signing (required)
        "platform_url": "https://moodle.university.edu",
        "deployment_id": "1",
    },
    {
        "name": "Canvas",
        "url_pattern": "https://canvas.college.edu",
        "client_id": "canvas-client-id",
        "token_url": "https://canvas.college.edu/login/oauth2/token",
        "platform_url": "https://canvas.college.edu",
        "private_key_path": "/secrets/lti/canvas_private_key.pem",
        "deployment_id": "2",
    },
]
```

### System Configuration Fields

| Field                  | Required | Default | Description                                                |
|------------------------|----------|---------|------------------------------------------------------------|
| `name`                 | Yes      | —       | Unique identifier for this platform.                       |
| `url_pattern`          | Yes      | —       | Base URL of the LTI platform, used for matching.           |
| `client_id`            | Yes      | —       | OAuth 2.0 client ID registered with the platform.          |
| `token_url`            | Yes      | —       | OAuth 2.0 token endpoint of the platform.                  |
| `private_key_path`     | Yes      | `""`    | Path to the PEM-encoded RSA private key file.              |
| `platform_url`         | No       | `""`    | Base URL of the platform.                                  |
| `deployment_id`        | No       | `""`    | LTI deployment ID.                                         |


## Configurable Hooks

Three hooks can be overridden to customize the sync behaviour:

### `resolve_lti_urls`

Resolves the LTI membership and lineitem URLs for a given platform, lecture and assignment.
**This hook must be configured** — the default raises `NotImplementedError`.

```python
def my_resolve_lti_urls(platform, lecture, assignment, submissions):
    """
    Args:
        platform: LTIPlatformConfig instance for the target system.
        lecture:  Serialized lecture dict.
        assignment: Serialized assignment dict.
        submissions: List of serialized submission dicts.

    Returns:
        dict with keys ``lineitems_url`` and ``membership_url``.
    """
    return {
        "lineitems_url": f"{platform.platform_url}/mod/lti/services.php/{platform.deployment_id}/lineitems",
        "membership_url": f"{platform.platform_url}/mod/lti/services.php/{platform.deployment_id}/memberships",
    }

c.LTISyncGrades.resolve_lti_urls = my_resolve_lti_urls
```

### `username_match`

Matches an LTI member to a grader submission.
**This hook must be configured** — the default always returns `False`.

```python
def my_username_match(member, submission, platform, log):
    """
    Args:
        member: LTI member dict from NRPS response.
        submission: Grader submission dict.
        platform: LTIPlatformConfig for the current system.
        log: Logger instance.

    Returns:
        True if the member matches the submission's user.
    """
    # Example: match by email
    email = member.get("email", "")
    username = submission.get("user", "").get("username", "")
    return email.split("@")[0] == username

c.LTISyncGrades.username_match = my_username_match
```

### `select_systems_for_sync`

Controls which platforms are synced to for a given lecture / assignment.
The default syncs to **all** configured platforms.

```python
def my_select_systems(lecture, assignment, submissions, platforms):
    """
    Args:
        lecture: Serialized lecture dict.
        assignment: Serialized assignment dict.
        submissions: List of serialized submission dicts.
        platforms: List of all LTIPlatformConfig instances.

    Returns:
        List of platform *names* to sync to.
    """
    # Example: only sync to platforms whose url_pattern appears in lecture code
    code = lecture.get("code", "")
    return [p.name for p in platforms if p.url_pattern in code]

c.LTISyncGrades.select_systems_for_sync = my_select_systems
```


## Key ID (`kid`) and JWT Signing

Each platform's JWT assertions include a `kid` (Key ID) header derived from the platform name:

```
kid = sha256(name.encode()).hexdigest()[:16]
```

This allows the receiving LTI platform to look up the correct public key from the JWKS endpoint.


## JWKS Endpoint

The grader service exposes a **public** JWKS (JSON Web Key Set) endpoint at:

```
GET /api/lti/jwks
```

This endpoint requires **no authentication** and returns the RSA public keys for all configured LTI platforms. Each key includes its `kid`, `alg` (`RS256`), and `use` (`sig`).

Example response:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "n": "...",
      "e": "AQAB",
      "kid": "b6f9abc123456789",
      "alg": "RS256",
      "use": "sig"
    }
  ]
}
```

Register this URL in your LTI platform's tool configuration so the platform can verify the grader service's JWT assertions.


## Helm Chart Configuration

When deploying with the Helm chart, configure LTI in `values.yaml`:

```yaml
ltiSyncGrades:
  enabled: true
  sync_on_feedback: false
  systems:
    - name: "MyMoodle"
      url_pattern: "https://moodle.university.edu"
      client_id: "my-client-id"
      token_url: "https://moodle.university.edu/mod/lti/token.php"
      platform_url: "https://moodle.university.edu"
      private_key_path: "/secrets/lti/private_key.pem"
      deployment_id: "1"
```


## API Endpoint

Trigger a grade sync via the REST API:

```
PUT /api/lectures/{lecture_id}/assignments/{assignment_id}/lti
```

The response contains results for each platform:

```json
{
  "synced_platforms": [
    {
      "platform": "MyMoodle",
      "syncable_users": 42,
      "synced_user": 40
    },
    {
      "platform": "Canvas",
      "syncable_users": 30,
      "synced_user": 30
    }
  ]
}
```

If a platform fails, its entry will include an `error` field:

```json
{
  "platform": "FailedPlatform",
  "error": "Unable to request token...",
  "syncable_users": 0,
  "synced_user": 0
}
```
