import math_func
import pytest
import sys


@pytest.mark.skipif(sys.version_info<=(3,3),reason="python version not met")
def test_add():
    assert math_func.add(7,3) == 10
    assert math_func.add(7) == 9
    assert math_func.add(5) == 7
    print("the calculation is running by -s")

@pytest.mark.number
def test_product():
    assert math_func.product(5,5) == 25
    assert math_func.product(5) == 10
    assert math_func.product(7) == 14

@pytest.mark.strings
def test_add_strings():
    result = math_func.add("hello","world")
    assert result is not None
    assert type(result) is str
    assert len(result) > 5

@pytest.mark.strings
def test_product_strings():
    result = math_func.product("hello")
    assert len(result) > 0
