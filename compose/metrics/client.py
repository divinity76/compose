import os
from enum import Enum

import requests
from docker import ContextAPI
from docker.transport import UnixHTTPAdapter

from compose.const import IS_WINDOWS_PLATFORM


class Status(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELED = "canceled"


class MetricsSource:
    CLI = "docker-compose"


if IS_WINDOWS_PLATFORM:
    METRICS_SOCKET_FILE = 'http+unix://\\\\.\\pipe\\docker_cli'
else:
    METRICS_SOCKET_FILE = 'http+unix:///var/run/metrics-docker-cli.sock'


class MetricsCommand(requests.Session):
    """
    Representation of a command in the metrics.
    """

    def __init__(self, command,
                 context_type=None, status=Status.SUCCESS,
                 source=MetricsSource.CLI, uri=None):
        super().__init__()
        self.command = "compose " + command if command else "compose --help"
        self.context = context_type or ContextAPI.get_current_context().context_type or 'moby'
        self.source = source
        self.status = status.value
        self.uri = uri or os.environ.get("METRICS_SOCKET_FILE", METRICS_SOCKET_FILE)
        self.mount("http+unix://", UnixHTTPAdapter(self.uri))

    def send_metrics(self):
        try:
            return self.post("http+unix://localhost/", json=self.to_map(), timeout=.05)
        except Exception as e:
            return e

    def to_map(self):
        return {
            'command': self.command,
            'context': self.context,
            'source': self.source,
            'status': self.status,
        }
