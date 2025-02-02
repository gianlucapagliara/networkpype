from collections.abc import Callable

from networkpype.rest.processor.base import RESTPreProcessor
from networkpype.rest.request import RESTRequest
from networkpype.time_synchronizer import TimeSynchronizer


class TimeSynchronizerRESTPreProcessor(RESTPreProcessor):
    """
    This pre processor is intended to be used in those connectors that require synchronization with the server time
    to accept API requests. It ensures the synchronizer has at least one server time sample before being used.
    """

    def __init__(self, synchronizer: TimeSynchronizer, time_provider: Callable):
        super().__init__()
        self._synchronizer = synchronizer
        self._time_provider = time_provider

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        await self._synchronizer.update_server_time_if_not_initialized(
            time_provider=self._time_provider()
        )
        return request
