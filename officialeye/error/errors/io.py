from officialeye.error.codes import ERR_IO_INVALID_SUPERVISION_ENGINE, ERR_IO_OPERATION_NOT_SUPPORTED_BY_DRIVER
from officialeye.error.error import OEError, ERR_MODULE_IO


class ErrIO(OEError):

    def __init__(self, code: int, code_text: str, while_text: str, problem_text: str, /):
        super().__init__(ERR_MODULE_IO, code, code_text, while_text, problem_text)


class ErrIOInvalidSupervisionEngine(ErrIO):
    def __init__(self, while_text: str, problem_text: str, /):
        super().__init__(
            ERR_IO_INVALID_SUPERVISION_ENGINE[0], ERR_IO_INVALID_SUPERVISION_ENGINE[1], while_text, problem_text)


class ErrIOOperationNotSupportedByDriver(ErrIO):
    def __init__(self, while_text: str, problem_text: str, /):
        super().__init__(
            ERR_IO_OPERATION_NOT_SUPPORTED_BY_DRIVER[0], ERR_IO_OPERATION_NOT_SUPPORTED_BY_DRIVER[1], while_text, problem_text)
