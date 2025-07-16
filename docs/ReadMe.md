# Sphinx documentation
## Requirements
``pip install -r requirements-docs.txt``
## Usage
Generate documentation:
``make html``

Delete documentation files:
``make clean``

## Hosting documentation pages locally

To locally host your documentation pages and watch changes firstly navigate to folder ``grader_service/docs``, then run following command line:

``(cd build/html/ && python3 -m http.server)``