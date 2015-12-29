import datetime as dt
import re
import string

from six.moves.urllib.parse import urlparse

OBJ_REQ_LINE_RE = re.compile(
    br"\A\s*(?P<method>HEAD|GET|POST|PUT|DELETE|PATCH|OPTIONS) (?P<uri>.*)\Z"
)

# Squid generates different logs when run in SMP mode, it tells us which child
# process each record is from. Strip that out.
KID_RE = re.compile(br"\A(\}\s*)?by kid\d+\s*(\{\s*)?", re.M)


def _split_records(records, sep):
    # TODO: Use StringIO-compatible parsing instead
    for record in records.split(sep):
        record = re.sub(KID_RE, b"", record).rstrip()
        if record:
            yield record


def parse_cache_object(buf):
    parsed = {}
    buf = buf.strip()
    lines = buf.split(b"\n")
    prefix, _, key = lines[0].partition(b" ")
    assert prefix == b"KEY" and key
    parsed["key"] = key.strip()
    for line in lines[1:]:
        match = re.match(OBJ_REQ_LINE_RE, line)
        if match:
            parsed["method"] = match.group("method")
            parsed["uri"] = match.group("uri")
            return parsed
    raise Exception("Couldn't find URI???")


def parse_cache_objects(buf):
    return (parse_cache_object(x) for x in _split_records(buf, b"\n\n"))


def parse_active_request(buf):
    parsed = {}
    buf = buf.strip()
    lines = buf.split(b"\n")
    in_connection = True
    for line in lines:
        if line.startswith(b"Connection: "):
            in_connection = True
            continue
        elif in_connection:
            if not re.match(br"\A\s+", line):
                in_connection = False

        if in_connection:
            key, _, val = (x.strip() for x in line.partition(b": "))
        else:
            key, _, val = line.partition(b" ")

        if key == b"uri":
            parsed["uri"] = val

        elif key == b"remote":
            parsed["client"] = val.split(b":", 1)[0]
        elif key == b"start":
            # TODO: use "seconds ago" instead? Not sure if this is tz-dependant.
            timeflot = float(val.split(b" ", 1)[0])
            parsed["date"] = dt.datetime.utcfromtimestamp(timeflot)
    return parsed


def parse_active_requests(buf):
    return (parse_active_request(x) for x in _split_records(buf, b"\n\n"))


def parse_netdb_entry(buf):
    return re.split(br"\s+", buf)[5:]


def parse_netdb_entries(buf):
    for entry in _split_records(buf, b"\n"):
        if entry.startswith(b"Network"):
            continue
        for host in parse_netdb_entry(entry):
            yield host


def parse_domain_from_uri(uri):
    if b"://" in uri:
        return urlparse(uri).hostname
    else:
        return uri.partition(b":")[0]
