"""Constants for the HK Public Transport integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "hkpublictransport"

# Polling
DEFAULT_SCAN_INTERVAL = timedelta(seconds=50)
MIN_SCAN_INTERVAL = timedelta(seconds=30)

# Cache TTLs
STATIC_CACHE_TTL = timedelta(hours=24)
ETA_CACHE_TTL = timedelta(seconds=25)

# Operators
OPERATOR_KMB = "kmb"
OPERATOR_LWB = "lwb"
OPERATOR_CTB = "ctb"
OPERATOR_NLB = "nlb"

OPERATORS = {
    OPERATOR_KMB: "KMB",
    OPERATOR_LWB: "LWB",
    OPERATOR_CTB: "Citybus",
    OPERATOR_NLB: "NLB",
}

# Status reasons
STATUS_OK = "ok"
STATUS_NO_SERVICE = "no_service"
STATUS_CACHED = "cached"
STATUS_API_ERROR = "api_error"
STATUS_API_TIMEOUT = "api_timeout"

# Attribute keys
ATTR_ROUTE = "route"
ATTR_OPERATOR = "operator"
ATTR_DIRECTION = "direction"
ATTR_SERVICE_TYPE = "service_type"
ATTR_DESTINATION = "destination"
ATTR_STOP_ID = "stop_id"
ATTR_STOP_NAME = "stop_name"
ATTR_STOP_SEQ = "stop_seq"
ATTR_NEXT_ARRIVAL = "next_arrival"
ATTR_SECOND_ARRIVAL = "second_arrival"
ATTR_THIRD_ARRIVAL = "third_arrival"
ATTR_IS_SCHEDULED = "is_scheduled"
ATTR_UPCOMING_ARRIVALS = "upcoming_arrivals"
ATTR_REMARK = "remark"
ATTR_LAST_UPDATED = "last_updated"
ATTR_DATA_SOURCE = "data_source"
ATTR_STATUS_REASON = "status_reason"

# Config flow
CONF_ROUTE = "route"
CONF_STOP_ID = "stop_id"
CONF_STOP_NAME = "stop_name"
CONF_OPERATOR = "operator"
CONF_DIRECTION = "direction"
CONF_SERVICE_TYPE = "service_type"
CONF_DESTINATION = "destination"
CONF_STOP_SEQ = "stop_seq"

# API base URLs
KMB_API_BASE = "https://data.etabus.gov.hk/v1/transport/kmb"
CTB_API_BASE = "https://rt.data.gov.hk/v2/transport/citybus"
NLB_API_BASE = "https://rt.data.gov.hk/v2/transport/nlb"

# Defaults
MAX_ARRIVALS = 5
REQUEST_TIMEOUT = 12  # seconds
