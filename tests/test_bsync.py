import datetime
from bsync import bsync
from lxml import etree


def test_initialize():
    b = bsync.BuildingSync()
    assert b is not None


def test_int_datatype():
    b = bsync.Sections.Section.Story(1)
    assert b is not None


def test_weather_data_station_id():
    """
    Added to ensure 'strange formulations', as described in https://github.com/BuildingSync/bsyncpy/issues/2
    can successfully be modeled with the bsyncpy library
    :return:
    """
    ws_id = bsync.WeatherDataStationID(IDref="an-id")
    assert ws_id is not None
    bldgs = bsync.Buildings(bsync.Buildings.Building(ws_id))
    xml_representation = etree.tostring(bldgs.toxml())
    assert (
        xml_representation.decode("utf-8")
        == '<Buildings><Building><WeatherDataStationID IDref="an-id"/></Building></Buildings>'
    )


def test_weather_station_name():
    """
    Added to ensure 'strange formulations', as described in https://github.com/BuildingSync/bsyncpy/issues/2
    can successfully be modeled with the bsyncpy library
    :return:
    """
    ws_name = bsync.WeatherStationName("A weather station")
    assert ws_name is not None
    bldgs = bsync.Sites(bsync.Sites.Site(ws_name))
    xml_representation = etree.tostring(bldgs.toxml())
    assert (
        xml_representation.decode("utf-8")
        == "<Sites><Site><WeatherStationName>A weather station</WeatherStationName></Site></Sites>"
    )


def test_datetime():
    """
    Added for https://github.com/BuildingSync/bsyncpy/issues/6
    """
    dt = datetime.datetime(2019, 1, 1, 0, 0, 0)
    ts = bsync.TimeSeriesData.TimeSeries.StartTimestamp(dt)
    assert ts is not None
    xml_representation = etree.tostring(ts.toxml())
    assert (
        xml_representation.decode("utf-8")
        == "<StartTimestamp>2019-01-01T00:00:00</StartTimestamp>"
    )


def test_date():
    """
    Added for https://github.com/BuildingSync/bsyncpy/issues/6
    """
    dt = datetime.date(2019, 1, 1)
    ts = bsync.RetrocommissioningDate(dt)
    assert ts is not None
    xml_representation = etree.tostring(ts.toxml())
    assert (
        xml_representation.decode("utf-8")
        == "<RetrocommissioningDate>2019-01-01</RetrocommissioningDate>"
    )


def test_time():
    """
    Added for https://github.com/BuildingSync/bsyncpy/issues/6
    """
    dt = datetime.time(0, 0, 0)
    ts = bsync.DayStartTime(dt)
    assert ts is not None
    xml_representation = etree.tostring(ts.toxml())
    assert xml_representation.decode("utf-8") == "<DayStartTime>00:00:00</DayStartTime>"


def test_gmonthday():
    """
    Added for https://github.com/BuildingSync/bsyncpy/issues/6
    """
    dt = datetime.date(2019, 1, 1)
    ts = bsync.ApplicableEndDateForDemandRate(dt)
    assert ts is not None
    xml_representation = etree.tostring(ts.toxml())
    assert (
        xml_representation.decode("utf-8")
        == "<ApplicableEndDateForDemandRate>01-01</ApplicableEndDateForDemandRate>"
    )
