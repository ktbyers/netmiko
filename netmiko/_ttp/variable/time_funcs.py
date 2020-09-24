import time


def get_time(*args, **kwargs):
    strformat = "%H:%M:%S"
    return time.strftime(strformat)


def get_date(*args, **kwargs):
    strformat = "%Y-%m-%d"
    return time.strftime(strformat)


def get_timestamp_ms(*args, **kwargs):
    strformat = "%Y-%m-%d %H:%M:%S.{ms}"
    return time.strftime(strformat).format(ms=str(time.time()).split(".")[-1][:3])


def get_timestamp(*args, **kwargs):
    strformat = "%Y-%m-%d %H:%M:%S"
    return time.strftime(strformat)


def get_time_ns(*args, **kwargs):
    # Return the current time in nanoseconds since the Epoch
    return time.time_ns()


def get_timestamp_iso(*args, **kwargs):
    # Returns timestamp in ISO format in UTC timezone
    # e.g.: 2020-04-07T05:27:17.613549+00:00
    import datetime

    class UTC(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return datetime.timedelta(0)

    utc = UTC()
    return datetime.datetime.now(utc).isoformat()