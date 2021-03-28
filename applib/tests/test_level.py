import pytest

from applib.model.level import *
from applib.model.item import Item


@pytest.fixture
def level():
    test_level = Level()
    return test_level


def test_batter_box_gives_you_batter(level):
    device = level.get_device('batter_box')
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'batter'
    assert device.is_finished

def test_batter_box_gives_you_batter_and_then_you_can_get_another(level):
    device = level.get_device('batter_box')
    for _ in range(1000):
        level.tick()
    level.interact(device)
    level.held_item is None
    level.interact(device)
    assert level.held_item.name == 'batter'
    assert device.is_finished


def test_batter_box_cannot_give_you_more_batter_if_holding_batter(level):
    device = level.get_device('batter_box')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('batter')
    level.interact(device)
    assert device.is_finished


def test_doughnut_improver_starts_off(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    assert not device.is_running


def test_doughnut_improve_runs_when_doughnut_inserted(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    assert device.is_running
    assert level.held_item is None

def test_doughnut_improver_makes_better_doughnut_when_finished(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    while not device.is_finished:
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'better_doughnut'

def test_doughnut_improver_cannot_retrieve_before_finished(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    level.tick()
    level.interact(device)
    assert device.is_running
    assert level.held_item is None

def test_doughnut_improver_will_not_take_doughnut_while_running(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    assert level.held_item.name == 'doughnut'

def test_doughnut_improver_cannot_take_batter(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('batter')
    level.interact(device)
    assert level.held_item.name == 'batter'
    assert not device.is_running

def test_doughnut_improver_duration(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    for _ in range(device.duration - 1):
        level.tick()
    assert not device.is_finished
    level.tick()
    assert device.is_finished


def test_doughnut_improver_duration_is_10_seconds(level):
    device = level.get_device('doughnut_improver')
    for _ in range(1000):
        level.tick()
    level.held_item = Item.get('doughnut')
    level.interact(device)
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert device.is_finished