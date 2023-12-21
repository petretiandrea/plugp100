import functools
import inspect


def requires_update(f):
    """Indicate that `update` should be called before accessing this method."""  # noqa: D202
    if inspect.iscoroutinefunction(f):

        @functools.wraps(f)
        async def wrapped(*args, **kwargs):
            self = args[0]
            if self._last_update is None or self.device_info is None:
                raise Exception("You need to await update() to access the data")
            return await f(*args, **kwargs)

    else:

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            self = args[0]
            if self._last_update is None or self.device_info is None:
                raise Exception("You need to await update() to access the data")
            return f(*args, **kwargs)

    # f.requires_update = True
    return wrapped
