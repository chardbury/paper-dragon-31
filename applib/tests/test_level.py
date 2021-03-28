import pytest

from applib.model.level import *
from applib.model.item import Item


@pytest.fixture
def level():
    test_level = Level()
    return test_level


def test_batter_box_gives_you_batter(level):
    for device in level.devices:
        if isinstance(device, BatterBox):
            break
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'batter'
    assert not device.is_finished


def test_batter_box_cannot_give_you_more_batter(level):
    for device in level.devices:
        if isinstance(device, BatterBox):
            break
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('batter')
    level.interact(device)
    assert device.is_finished
