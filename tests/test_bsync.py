from bsync import bsync

def test_initialize():
    b = bsync.BuildingSync()
    assert b is not None