import pytest

from applib.model.level import *


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
    level.held_item = batter
    level.interact(device)
    assert device.is_finished

def test_doughtnut_improver_starts_off(level):
    for device in level.devices:
        if isinstance(device, DoughnutImprover):
            break
    for _ in range(1000):
        level.tick()
    assert not device.is_running

def test_doughnut_improve_runs_when_doughnut_inserted(level):
    for device in level.devices:
        if isinstance(device, DoughnutImprover):
            break
    for _ in range(1000):
        level.tick()
    level.held_item = doughnut
    level.interact(device)
    assert device.is_running
    assert level.held_item is None



    