from typing import Iterable, Union

'''
In Kleene's three-valued logic there are possible values are True, False and Unknown.
Unknown is represented by None.
Examples:
    or3(True, None) -> True
    or3(False, None) -> None
    and3(True, None) -> None
    and3(False, None) -> False
'''


def or3(ls: Iterable[Union[bool, None]]) -> Union[bool, None]:
    unknown_flag = False
    for v in ls:
        if v: return True
        if v is None: unknown_flag = True
    if unknown_flag:
        return None
    return False        

def test_or3() -> None:
    # test that it works on generators
    assert or3((i for i in (None, False, True))) == True
    assert or3((False, False)) == False
    assert or3((i for i in (None, False, None))) == None

    
def and3(ls: Iterable[Union[bool, None]]) -> Union[bool, None]:
    unknown_flag = False
    for v in ls:
        if v == False: return False
        if v is None: unknown_flag = True
    if unknown_flag:
        return None
    return True

def test_and3() -> None:
    assert and3((i for i in (None, True, False))) == False
    assert and3((True, True)) == True
    assert and3((i for i in (None, True, None))) == None
