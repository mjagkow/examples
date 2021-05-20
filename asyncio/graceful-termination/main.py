import asyncio
import signal
import logging
from functools import partial
from typing import Set, Union

log = logging.getLogger(__name__)


def setup_logging(level: Union[int, str]):
    _log = logging.getLogger(__name__)
    _log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s: %(message)s'))
    handler.setLevel(level)
    _log.addHandler(handler)
    _log.propagate = False


class GracefulTerminationExample:
    def __init__(self):
        self._tasks: Set[asyncio.Task] = set()

    def _handle_signal(self, signame, loop):
        log.debug(f'Received {signame}')

        for task in list(self._tasks):
            log.debug(f'Cancelling task {task.get_coro().__qualname__}')
            task.cancel()
            self._tasks.remove(task)

    async def run_once(self, sleep: float = 3):
        log.info(f"Sleeping {sleep}s")
        await asyncio.sleep(sleep)

    async def _cron_loop(self):
        while True:
            await self.run_once()

    async def run(self):
        loop = asyncio.get_running_loop()

        for signame in {'SIGINT', 'SIGTERM'}:
            loop.add_signal_handler(
                getattr(signal, signame),
                partial(self._handle_signal, signame, loop)
            )

        task = asyncio.create_task(self._cron_loop())
        self._tasks.add(task)
        try:
            return (await asyncio.gather(task))[0]
        except asyncio.CancelledError:
            pass
        log.info('Bye!')


def main():
    setup_logging("DEBUG")
    asyncio.get_event_loop().run_until_complete(GracefulTerminationExample().run())


if __name__ == '__main__':
    main()
