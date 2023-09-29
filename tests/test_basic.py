from lxml import etree
import os
from bsyncpy import bsync


def test_writefile():
    # remove old file
    if os.path.exists("output.xml"):
        os.remove("output.xml")
    assert os.path.exists("output.xml") == False

    # Create a root and set the version attribute
    root = bsync.BuildingSync()
    root.set("version", "2.5.0")

    # Valid element attributes can also be passed in as kwargs
    f = bsync.Facilities(bsync.Facilities.Facility(ID="Facility-42"))

    # Add the facilities.facility elements to the root
    root += f

    # write the document to disk
    with open("output.xml", "wb+") as f:
        output = etree.tostring(
            root.toxml(),
            pretty_print=True,
            doctype='<?xml version="1.0" encoding="UTF-8"?>',
        )
        f.write(output)

    # verify that it is written out
    assert os.path.exists("output.xml") == True

    with open("output.xml") as f:
        if '<BuildingSync version="2.5.0">' in f.read():
            assert True
        else:
            assert False, "Could not find correct BuildingSync version in file"
