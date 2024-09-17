from typing import Collection, Union
import pytest

'''
In Kleene's three-valued logic there are possible values are True, False and Unknown.
Unknown is represented by None.
Examples:
    or3(True, None) -> True
    or3(False, None) -> None
    and3(True, None) -> None
    and3(False, None) -> False
'''


def or3(ls: Collection[Union[bool, None]]) -> Union[bool, None]:
    if ls is iter(ls):
        raise Exception("You gave me an iterator instead of a Collection!")
    if any(ls):
        return True
    if all(i == False for i in ls):
        return False
    return None


def test_or3() -> None:
    assert or3([None, False, True]) == True
    assert or3((False, False)) == False
    assert or3([None, False, None]) == None

    # I would add this test, but mypy is gonna complain.
    # And then again, this exception is just a hack to help people who aren't using mypy,
    # not really a requirement for the function
    # with pytest.raises(Exception):
    #     or3(i for i in [None, False, None])


def and3(ls: Collection[Union[bool, None]]) -> Union[bool, None]:
    if ls is iter(ls):
        raise Exception("You gave me an iterator instead of a Collection!")
    if any(v == False for v in ls):
        return False
    if all(i for i in ls):
        return True
    return None


def test_and3() -> None:
    assert and3([None, True, False]) == False
    assert and3((True, True)) == True
    assert and3([None, True, None]) == None
