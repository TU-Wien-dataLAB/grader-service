# Authentication & Authorization Configuration

The Grader Service supports two distinct modes for handling authentication and authorization, designed to integrate with JupyterHub in educational environments. Each mode offers a different balance of simplicity and flexibility depending on your infrastructure and requirements.

In the Grader Service, users are associated with lectures and can hold one of the following roles:

- `instructor`
- `tutor`
- `student`

These roles determine access permissions within the app and are stored in the internal user model of the Grader Service.

### Mode 1: JupyterHub Provides API Token (Simple Mode)

In this simpler mode, **JupyterHub starts first**, and provides the user's API token to the Grader Service at server startup. The Grader Service then queries the JupyterHub API to obtain information about the current user (e.g., `username`, `groups`) and stores this in its own database.

**Architecture Overview:**

**Advantages:**

- Easy to set up and understand
- No need to manage additional OAuth flows

**Limitations:**

- Works only with **one JupyterHub instance**
- The Grader Service can only access information that JupyterHub exposes (e.g., groups)
- Less flexible for multi-hub or cross-institutional setups


### Mode 2: Grader Service Wraps JupyterHub (Advanced Mode)

In this configuration, the Grader Service acts as the **primary authentication gateway**, handling authentication via an external OAuth provider (or similar mechanism). Once authenticated, it launches JupyterHub instances and authenticates to them using **OAuth2**.

**Architecture Overview:**

**Advantages:**

- Centralized user authentication across **multiple JupyterHub deployments**
- Fine-grained control over user roles and access in the Grader Service
- Can enrich user records with external data (e.g., institutional systems)

**Considerations:**

- More complex setup
- Requires configuring both the Grader Service and JupyterHub for OAuth2 communication

---

### Configuration

Grader Service uses **[traitlets](https://traitlets.readthedocs.io/)** for configuration. Both authentication modes are fully supported through traitlet-based configuration options. Refer to the configuration section below for code examples and setup instructions:

- [Configuration for Mode 1: JupyterHub API Token](#)
- [Configuration for Mode 2: Grader Wraps JupyterHub](#)

---

Choose the mode that best fits your deployment scenario. For small-to-medium-scale or single-hub deployments, Mode 1 may suffice. For larger, multi-hub, or institutionally integrated setups, Mode 2 offers a more robust solution.
