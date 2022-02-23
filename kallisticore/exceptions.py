from typing import Optional, List

from kallisticore.models.trial import TrialStepsType


class KallistiCoreException(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


# TODO: change this to UnknownNamespaceName to match terminology.
class UnknownModuleName(KallistiCoreException):
    pass


class CouldNotFindFunction(KallistiCoreException):
    pass


class FailedAction(KallistiCoreException):
    pass


class InvalidCredentialType(KallistiCoreException):
    def __init__(self, credential_type: Optional[str],
                 *args: Optional[List]) -> None:
        message = "Invalid credential type: " + str(credential_type)
        super().__init__(message, *args)


class CredentialNotFound(KallistiCoreException):
    def __init__(self, source, **kwargs) -> None:
        message = "Credential not found. Source: {}, Details: {}"\
            .format(source, kwargs)
        super().__init__(message=message)


class EnvironmentValueNotFound(KallistiCoreException):
    def __init__(self, name, **kwargs) -> None:
        message = "Environment value not found. Name: {}".format(name)
        super().__init__(message=message)


class InvalidPlatformType(KallistiCoreException):
    def __init__(self, platform_type: Optional[str],
                 *args: Optional[List]) -> None:
        message = "Invalid platform type: " + str(platform_type)
        super().__init__(message, *args)


class InvalidExpectOperator(KallistiCoreException):
    def __init__(self, operator: str, *args: Optional[List]) -> None:
        message = "Invalid operator: " + str(operator)
        super().__init__(message, *args)


class FailedExpectation(KallistiCoreException):
    def __init__(self, message: str, *args: Optional[List]) -> None:
        message = "Expectation failed({})".format(message)
        super().__init__(message, *args)

    def __str__(self):
        return self.message


class KeyNotFoundException(KallistiCoreException):
    pass


class InvalidHttpProbeMethod(KallistiCoreException):
    pass


class InvalidHttpRequestMethod(KallistiCoreException):
    pass


class MissingParameterValueError(KallistiCoreException):
    pass


class LicenseFetchError(Exception):
    pass


class StepsExecutionError(KallistiCoreException):
    def __init__(self, step_type: TrialStepsType, *args, **kwargs) -> None:
        self.step_type = step_type
        message = "\"" + step_type.value + "\" failed."
        super().__init__(message, *args)

    def __str__(self):
        return "[in: " + self.step_type.value + ", reason: " + \
               str(self.__cause__) + "]"

    def is_pre_steps_exception(self):
        return self.step_type == TrialStepsType.PRE
