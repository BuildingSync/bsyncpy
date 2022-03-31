# bsyncpy

![Build Status](https://github.com/BuildingSync/bsyncpy/actions/workflows/ci.yml/badge.svg?branch=develop)

Current BuildingSync version: `2.4.0`.

## Generating
- `poetry install`
- `poetry run pre-commit install`
- Download, copy, or curl a BuildingSync schema into `bsyncpy/bsyncpy`
  - `curl -L -o bsyncpy/BuildingSync-2.4.xsd https://github.com/BuildingSync/schema/releases/download/v2.4.0/BuildingSync.xsd`
- cd into `bsyncpy/bsyncpy`
- Run generator: `poetry run python bsyncpy_generator.py BuildingSync-2.4.xsd`
- Go back to the root `bsyncpy` and run tests: `poetry run pytest`
- Make sure formatting is good: `poetry run pre-commit run --all-files`
- On commit, pre-commit should run again

## Simple example

*Input*
```python
from lxml import etree
from bsyncpy import bsync

# Create a root and set the version attribute
root = bsync.BuildingSync()
root.set('version', '2.4.0')

# Valid element attributes can also be passed in as kwargs
f = bsync.Facilities(bsync.Facilities.Facility(ID='Facility-1'))

# Add the facilities.facility elements to the root
root += f

# write the document to disk
with open('output.xml', 'wb+') as f:
    output = etree.tostring(root.toxml(), pretty_print=True, doctype='<?xml version="1.0" encoding="UTF-8"?>')
    f.write(output)
```

*Output*
```xml
<?xml version="1.0" encoding="UTF-8"?>
<BuildingSync version="2.4.0">
  <Facilities>
    <Facility ID="Facility-1"/>
  </Facilities>
</BuildingSync>
```

## Comprehensive example

Check out our example Jupyter Notebook [here](https://nbviewer.jupyter.org/github/BuildingSync/schema/blob/develop-v2/docs/notebooks/bsync_examples/Small-Office-Level-1.ipynb).


# Updating Version

* See the notes above on downloading and generating the new bsync.py file. 
* Bump version in `pyproject.toml` file
* Add/update CHANGELOG entry
* Update (or add) generator test in `.github/ci.yml`
* Update this README with the latest version of testing.