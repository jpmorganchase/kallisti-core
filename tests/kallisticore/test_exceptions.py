from unittest import TestCase

from kallisticore.exceptions import KallistiCoreException, FailedAction, \
    InvalidCredentialType, CredentialNotFound, StepsExecutionError
from kallisticore.lib.credential import EnvironmentUserNamePasswordCredential
from kallisticore.models.trial import TrialStepsType


class TestKallistiCoreException(TestCase):
    def test_initialization(self):
        error_message = "sample error message"
        exception = KallistiCoreException(message=error_message)

        self.assertEqual(error_message, exception.message)
        self.assertIsInstance(exception, KallistiCoreException)


class TestFailedAction(TestCase):
    def test_initialization(self):
        error_message = "sample error message"
        exception = FailedAction(message=error_message)

        self.assertEqual(error_message, exception.message)
        self.assertIsInstance(exception, FailedAction)
        self.assertIsInstance(exception, KallistiCoreException)


class TestInvalidCredentialType(TestCase):
    def test_initialization(self):
        credential_type = "INVALID"
        exception = InvalidCredentialType(credential_type)

        self.assertEqual("Invalid credential type: " + credential_type,
                         exception.message)
        self.assertIsInstance(exception, InvalidCredentialType)
        self.assertIsInstance(exception, KallistiCoreException)


class TestCredentialNotFound(TestCase):
    def test_initialization(self):
        source = EnvironmentUserNamePasswordCredential.__name__
        exception = CredentialNotFound(source, username_key='user',
                                       password_key='pass')

        self.assertEqual("Credential not found. Source: " + source +
                         ", Details: {'username_key': 'user'"
                         ", 'password_key': 'pass'}",
                         exception.message)
        self.assertIsInstance(exception, CredentialNotFound)
        self.assertIsInstance(exception, KallistiCoreException)


class TestStepsExecutionError(TestCase):
    def test_initialization(self):
        exception = StepsExecutionError(TrialStepsType.PRE)

        self.assertEqual(TrialStepsType.PRE, exception.step_type)
        self.assertEqual("\"pre_steps\" failed.", exception.message)
        self.assertIsInstance(exception, StepsExecutionError)
        self.assertIsInstance(exception, KallistiCoreException)

    def test_str(self):
        exception = StepsExecutionError(TrialStepsType.PRE)
        exception.__cause__ = RuntimeError("some-error")

        self.assertEqual("[in: pre_steps, reason: some-error]", str(exception))

    def test_is_pre_steps_exception_when_step_type_is_pre_steps(self):
        exception = StepsExecutionError(TrialStepsType.PRE)
        exception.__cause__ = RuntimeError("some-error")

        self.assertTrue(exception.is_pre_steps_exception())

    def test_is_pre_steps_exception_when_step_type_is_post_steps(self):
        exception = StepsExecutionError(TrialStepsType.POST)
        exception.__cause__ = RuntimeError("some-error")

        self.assertFalse(exception.is_pre_steps_exception())

    def test_is_pre_steps_exception_when_step_type_is_steps(self):
        exception = StepsExecutionError(TrialStepsType.STEPS)
        exception.__cause__ = RuntimeError("some-error")

        self.assertFalse(exception.is_pre_steps_exception())
