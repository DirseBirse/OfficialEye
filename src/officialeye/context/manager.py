from types import TracebackType
from typing import Union

from officialeye.context.context import Context
from officialeye.error.error import OEError
from officialeye.error.errors.internal import ErrInternal


class ContextManager:

    def __init__(self, /, *, handle_exceptions: bool = True, visualization_generation: bool = False,
                 export_directory: Union[str, None] = None):

        self._context: Union[Context, None] = None

        self._handle_exceptions = handle_exceptions

        self.visualization_generation = visualization_generation

        self.export_directory = export_directory

    def __enter__(self) -> Context:

        if self._context is not None:
            raise ErrInternal(
                "while entering an officialeye context.",
                "The present context manager has already got an associated context. Are you trying to reuse the context manager?"
            )

        self._context = Context(self, visualization_generation=self.visualization_generation)

        return self._context

    def __exit__(self, exception_type: any, exception_value: BaseException, traceback: TracebackType):

        if self._context is None:
            raise ErrInternal(
                "while leaving an officialeye context.",
                "The present context manager has no context associated with it."
            )

        self._context.dispose()

        if not self._handle_exceptions:
            return

        # handle the possible exception
        if exception_value is None:
            # there is no exception, nothing to handle
            return

        if isinstance(exception_value, OEError):
            oe_error = exception_value
        else:
            oe_error = ErrInternal(
                "while leaving an officialeye context.",
                "An internal error occurred.",
                external_cause=exception_value
            )

        self._context.get_io_driver().output_error(oe_error)

        # tell python that we have handled the exception ourselves
        return True
