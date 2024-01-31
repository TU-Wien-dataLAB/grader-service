# Git Server

This package contains handlers that implement a git remote repository
and can accept arbitrary push or pull requests.

# Authentication

To be authenticated with the server, git has to pass the JupyterHub token of the user as authentication. 
Since git only uses basic auth, the token has to be passed as the password with arbitrary username. 
See the official [git documentation](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage) for configuration options.
