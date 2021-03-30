import pytest

import applib

from applib.constants import TICK_LENGTH
from applib.model import device
from applib.model import entity
from applib.model import item
from applib.model import level


class ExampleLevel(level.Level):

    device_specification = [
        (device.BatterTray, 0.0, 0.0),
        (device.DoughnutFryer, 0.0, 0.0),
        (device.Plate, 0.0, 0.0),
        (device.Bin, 0.0, 0.0),
    ]

    


@pytest.fixture
def level():
    example_level = ExampleLevel()
    return example_level


def test_batter_tray_gives_you_batter(level):
    device = level.get_device('batter_tray')
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'batter'
    assert device.is_finished

def test_batter_tray_gives_you_batter_and_then_you_can_get_another(level):
    device = level.get_device('batter_tray')
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'batter'
    level.held_item = item.Doughnut(level)
    level.interact(device)
    assert level.held_item.name == 'doughnut'
    assert device.is_finished


def test_doughnut_fryer_starts_off(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    assert not device.is_running


def test_doughnut_improve_runs_when_doughnut_inserted(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    assert device.is_running
    assert level.held_item is None

def test_doughnut_fryer_makes_doughnut_cooked_when_finished(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'doughnut'

def test_doughnut_fryer_cannot_retrieve_before_finished(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    level.tick()
    level.interact(device)
    assert device.is_running
    assert level.held_item is None

def test_doughnut_fryer_will_not_take_batter_while_running(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    assert level.held_item.name == 'batter'

def test_doughnut_fryer_cannot_take_doughnut(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Doughnut(level)
    level.interact(device)
    assert level.held_item.name == 'doughnut'
    assert not device.is_running

def test_doughnut_fryer_duration(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    for _ in range(device.duration_ticks - 1):
        level.tick()
    assert not device.is_finished
    level.tick()
    assert device.is_finished


def test_doughnut_fryer_duration_is_10_seconds(level):
    device = level.get_device('doughnut_fryer')
    for _ in range(1000):
        level.tick()
    level.held_item = item.Batter(level)
    level.interact(device)
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert device.is_finished

def test_customer_added(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.Doughnut(level)))
    assert len(level.customers) == 1

def test_customer_removed(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.Doughnut(level)))
    for _ in range (level.customers[0].patience):
        level.tick()
    assert len(level.customers) == 0 and level.sad_customer == 1

def test_customer_added_with_one_item_order(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.Doughnut(level)))
    assert len(level.customers[0].order.items) == 1

def test_customer_serve_right_item(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.Doughnut(level)))
    level.held_item = item.Doughnut(level)
    level.interact(level.customers[0])
    assert len(level.customers[0].order.items) == 0
    level.tick()
    assert level.happy_customer == 1 and level.sad_customer == 0

def test_customer_serve_wrong_item(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.Doughnut(level)))
    level.held_item = item.Batter(level)
    level.interact(level.customers[0])
    assert len(level.customers[0].order.items) == 1
    level.tick()
    assert level.happy_customer == 0 and level.sad_customer == 0

def test_plate_recipes(level):
    from applib.model.level import Customer, Order
    device = level.get_device('plate')
    level.held_item = item.Doughnut(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.Doughnut)
    level.held_item = item.Glaze(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.DoughnutGlazed)
    level.interact(device)
    assert isinstance(level.held_item, item.DoughnutGlazed)
    assert device.current_item is None

def test_bin(level):
    from applib.model.level import Customer, Order
    device = level.get_device('bin')
    level.tick()
    level.held_item = item.Doughnut(level)
    assert isinstance(level.held_item, item.Doughnut)
    level.interact(device)
    assert level.held_item is None
    level.held_item = item.Doughnut(level)
    level.interact(device)
    assert level.held_item is None
    level.interact(device)
    assert level.held_item is None
    assert device.current_item is None


def test_bin_destroys_items(level):
    device = level.get_device('bin')
    test_item = item.Doughnut(level)
    assert test_item.level is level
    assert test_item in level.entities
    level.held_item = test_item
    level.interact(device)
    assert test_item.level is None
    assert test_item not in level.entities


def test_plate_destroys_previous_item(level):
    plate = level.get_device('plate')
    doughnut = item.Doughnut(level)
    glaze = item.Glaze(level)
    assert doughnut.level is level
    assert doughnut in level.entities
    assert glaze.level is level
    assert glaze in level.entities
    level.held_item = doughnut
    level.interact(plate)
    level.held_item = glaze
    level.interact(plate)
    assert doughnut.level is None
    assert doughnut not in level.entities
    assert glaze.level is None
    assert glaze not in level.entities
