# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
import inspect
import typing
from traitlets import Integer, TraitError, validate, Bool, Callable
from traitlets.config import SingletonConfigurable
from asyncio import Queue


class GraderExecutor(SingletonConfigurable):

    n_concurrent_tasks = Integer(default_value=5,
                                 allow_none=False).tag(config=True)

    resubmit_cancelled_tasks = Bool(default_value=False,
                                    allow_none=False).tag(config=True)

    get_event_loop = Callable(default_value=asyncio.get_event_loop,
                              allow_none=False).tag(config=True)

    async def task_executor(self):
        coro, on_finish = (None, None)
        try:
            while self.running:
                coro, on_finish = await self.queue.get()
                try:
                    await coro()
                    if on_finish is not None:
                        if inspect.iscoroutinefunction(on_finish):
                            await on_finish()
                        else:
                            on_finish()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.log.error(
                        f"An exception ({e.__class__.__name__}) \
                        was raised when executing task {coro.__name__}!",
                        exc_info=e)
                self.queue.task_done()
        except asyncio.CancelledError:
            if self.resubmit_cancelled_tasks and coro is not None:
                self.queue.put_nowait((coro, on_finish))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.queue = Queue()
        self.loop = self.get_event_loop()
        self.workers = [self.loop.create_task(self.task_executor())
                        for _ in range(self.n_concurrent_tasks)]

    def submit(self, task: typing.Callable, on_finish: typing.Callable = None):
        """Submit a task to be processed by the executor.
        :param task: The task to be executed.
        :param on_finish: Callable that is executed
                        when submitted task finishes.
                        Can be synchronous or asynchronous call.
        """
        self.queue.put_nowait((task, on_finish))

    def cancel_tasks(self):
        """Immediately cancel all tasks being executed.
        """
        for worker in self.workers:
            worker.cancel()
        self.running = False

    async def stop(self, timeout=5):
        """Wait for tasks to finish within the timout
        and cancel remaining tasks.

        :param timeout: Timeout in seconds.
        """
        self.running = False
        done, pending = await asyncio.wait(self.workers, timeout=timeout)
        for fut in pending:
            fut.cancel()
        self.workers = None

    def start(self):
        """Restart the executor.
        If it is already running this has no effect.
        """
        if self.running:
            return
        self.running = True
        self.workers = [self.loop.create_task(self.task_executor())
                        for _ in range(self.n_concurrent_tasks)]

    def remove_queued_tasks(self):
        """
        Remove all items in the queue.
        """
        self.queue = Queue()

    @validate("n_concurrent_tasks")
    def _validate_n_tasks(self, proposal):
        n = proposal.value
        if n <= 0:
            raise TraitError(f"Num concurrent tasks has to be > 0, got: {n}")
        return n


if __name__ == "__main__":
    async def main():
        from random import randint
        from traitlets.config import LoggingConfigurable
        from traitlets import log as traitlets_log
        import sys
        import logging

        def demo_task(code):
            class DemoExec(LoggingConfigurable):
                def __init__(self, **kwargs):
                    self._setup_logger()
                    super().__init__(**kwargs)

                    # self.log = logging.getLogger()  # THIS WORKS?!?!

                    log: logging.Logger = self.log
                    print(f"name: {log.name}, handlers: {log.handlers},"
                          f"disabled: {log.disabled}, parent: {log.parent}")

                async def wait_task(self):
                    wait_time = randint(1, 3)
                    sys.stdout.flush()
                    self.log.error('running {} will take {} second(s)'
                                   .format(code, wait_time))
                    # I/O, context will switch to main function
                    await asyncio.sleep(wait_time)
                    self.log.error('ran {}'.format(code))

                def _setup_logger(self):
                    stream_handler = logging.StreamHandler
                    traitlet_logger = traitlets_log.get_logger()
                    traitlet_logger.removeHandler(traitlet_logger.handlers[0])
                    traitlet_logger.setLevel("INFO")
                    traitlets_handler = stream_handler(stream=sys.stdout)
                    traitlets_handler.setFormatter(
                        logging.Formatter(
                            "[%(asctime)s] %(levelname)-8s "
                            "%(name)-13s %(module)-15s %(message)s"
                        )
                    )
                    traitlet_logger.addHandler(traitlets_handler)

            return DemoExec()

        GraderExecutor.n_concurrent_tasks = 3
        GraderExecutor.resubmit_cancelled_tasks = True
        executor = GraderExecutor.instance()
        for i in range(9):
            task = demo_task(i).wait_task

            async def p():
                await asyncio.sleep(0.5)
                print(f"Queue Size: {executor.queue.qsize()}")

            executor.submit(task, p)
        await asyncio.sleep(4)
        print("CANCEL")
        executor.cancel_tasks()
        print(executor.queue.qsize())
        executor.start()

        await asyncio.sleep(10)


    # need running asyncio loop
    asyncio.run(main())
