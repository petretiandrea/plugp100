# Get from pyEffects library
from typing import Callable, Generic, List, Type, TypeVar, Union, overload

A = TypeVar("A", covariant=True)
B = TypeVar("B")


class Try(Generic[A]):
    value: A
    biased: bool

    @staticmethod
    @overload
    def of(func_or_value: Callable[[], B]) -> "Try[B]":
        ...

    @staticmethod
    @overload
    def of(func_or_value: B) -> "Try[B]":
        ...

    @staticmethod
    def of(func_or_value: Union[B, Callable[[], B]]) -> "Try[B]":
        """Constructs a :class:`Try <Try>`.

        :param func_or_value: function or value to construct a new :class:`Try` object
        :rtype: pyEffects.Try

        Usage::

          >>> Try.of(lambda: 5)
          Success(5)
          >>> Try.of("abc")
          Success(abc)
          >>> def error():
          ...   raise Exception("failed")
          ...
          >>> Try.of(error)
          Failure(failed)
        """
        try:
            value = func_or_value() if hasattr(func_or_value, "__call__") else func_or_value  # type: ignore
            return Success(value)  # type: ignore
        except Exception as err:
            return Failure(err)

    def map(self, func: Callable[[A], B]) -> "Try[B]":
        if not hasattr(func, "__call__"):
            raise TypeError("map expects a callable")

        def wrapped(x: A) -> "Try[B]":
            return self.of(func(x))

        return self.flat_map(wrapped)

    def flat_map(self, func: Callable[[A], "Try[B]"]) -> "Try[B]":
        """Flatmaps a function for :class:`Try <Try>`.

        :param func: function returning a pyEffects.Try to apply to flat_map.
        :rtype: pyEffects.Try

        Usage::

          >>> Success(5).flat_map(lambda v: Success(v * v))
          Success(25)
        """
        if not hasattr(func, "__call__"):
            raise TypeError("Try.flat_map expects a callable")
        if self.is_success():
            return func(self.value)
        else:
            return self  # type: ignore

    def recover(
        self, err: Type[Exception], recover: Union[B, Callable[[], B]]
    ) -> "Try[B]":
        """Recover from an exception for :class:`Try <Try>`.

        :param err: The class of exception to recover from.
        :param recover: The function to apply when recovering from an exception
        :rtype: pyEffects.Try

        Usage::

          >>> def error():
          ...   raise RuntimeError("failed")
          ...
          >>> Try.of(error).recover(RuntimeError, "abc")
          Success(abc)
        """
        if self.is_failure() and isinstance(self.value, err):
            return Try.of(recover)
        return self  # type: ignore

    def recovers(
        self, errs: List[Type[Exception]], recover: Union[B, Callable[[], B]]
    ) -> "Try[B]":
        """Recover from an exception for :class:`Try <Try>`.

        :param errs: A list of classes of exceptions to recover from.
        :param recover: The function to apply when recovering from an exception
        :rtype: pyEffects.Try

        Usage::
          >>> def error():
          ...   raise RuntimeError("failed")
          ...
          >>> Try.of(error).recovers([RuntimeError, NotImplementedError], "abc")
          Success(abc)
        """
        if not isinstance(errs, list):
            raise TypeError("Try.recovers expects a list of errors as the 1nd arg")
        if self.is_failure() and any([isinstance(self.value, e) for e in errs]):
            return Try.of(recover)
        return self  # type: ignore

    def error(self) -> Exception:  # type: ignore
        """Recover the exception for :class:`Try <Try>`.

        :rtype: pyEffects.Try

        Usage::

          >>> def error():
          ...  raise RuntimeError()
          ...
          >>> Try.of(error).error()
          RuntimeError()
        """
        if self.is_failure():
            return self.value  # type: ignore

    def is_success(self) -> bool:
        """Return is success for :class:`Try <Try>`.

        :rtype: pyEffects.Try

        Usage::

          >>> Failure(RuntimeError()).is_success()
          False
        """
        return self.biased

    def is_failure(self) -> bool:
        """Return is failure for :class:`Try <Try>`.

        :rtype: pyEffects.Try

        Usage::

          >>> Failure(RuntimeError()).is_failure()
          True
        """
        return not self.is_success()

    def foreach(self, func: Callable[[A], B]) -> None:
        if not hasattr(func, "__call__"):
            raise TypeError("foreach expects a callable")
        self.map(func)

    def get(self) -> A:
        if self.biased:
            return self.value
        raise TypeError("get cannot be called on this class")

    def get_or_raise(self) -> A:
        if self.is_failure():
            raise self.value
        else:
            return self.value

    def get_or_else(self, v: A) -> A:
        if self.biased:
            return self.value
        else:
            return v

    def or_else_supply(self, func: Callable[[], A]) -> A:
        if not hasattr(func, "__call__"):
            raise TypeError("or_else_supply expects a callable")
        if self.biased:
            return self.value
        else:
            return func()

    def or_else(self, other: "Try[A]") -> "Try[A]":
        if not isinstance(other, Try):
            raise TypeError("or_else can only be chained with other Monad classes")
        if self.biased:
            return self
        else:
            return other


class Failure(Try[A]):
    def __init__(self, value: Exception) -> None:
        self.value = value  # type: ignore
        self.biased = False

    def __repr__(self) -> str:
        return "Failure(" + str(self.value) + ")"


class Success(Try[A]):
    def __init__(self, value: A) -> None:
        self.value = value
        self.biased = True

    def __repr__(self) -> str:
        return "Success(" + str(self.value) + ")"
