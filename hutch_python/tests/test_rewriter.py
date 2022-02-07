import pytest

from ..rewriter import rewriter


def a():
    yield 1


def b():
    yield 2


def c():
    yield 3


@rewriter
def my_plan():
    if True:
        a.run()
    if False:
        b.run()
    yield from c()


@rewriter
def my_plan_raises():
    if True:
        a.run()
    yield from c()
    raise ValueError("test")


def test_rewriter():
    assert list(my_plan()) == [1, 3]


def test_rewriter_raises():
    with pytest.raises(ValueError) as ex:
        list(my_plan_raises())
    assert ex.traceback[-1].lineno == 32
