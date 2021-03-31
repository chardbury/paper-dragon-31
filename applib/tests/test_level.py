import pytest

import applib

from applib.constants import TICK_LENGTH
from applib.model import device
from applib.model import entity
from applib.model import item
from applib.model import level


class ExampleLevel(level.Level):

    device_specification = [
        (device.Dough, 0.0, 0.0),
        (device.Cooking, 0.0, 0.0),
        (device.Plate, 0.0, 0.0),
        (device.Bin, 0.0, 0.0),
    ]

    customer_specification = [
        (5, [item.DoughnutCooked]),
        (15, [item.DoughnutCooked, item.DoughnutGlazed])
    ]

    customer_spaces_specification = 2


@pytest.fixture
def level():
    example_level = ExampleLevel()
    return example_level


def test_dough_station_gives_you_doughnuts(level):
    device = level.get_device('station_dough')
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'doughnut_uncooked'
    assert device.is_finished

def test_dough_station_if_holding_something(level):
    device = level.get_device('station_dough')
    level.tick()
    original_item = item.DoughnutCooked(level)
    level.held_item = original_item
    level.interact(device)
    assert level.held_item is original_item

def test_cooking_station_starts_off(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    assert not device.is_running

def test_doughnut_improve_runs_when_doughnut_inserted(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    assert device.is_running
    assert level.held_item is None

def test_doughnut_fryer_makes_doughnut_cooked_when_finished(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    for _ in range(1000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'doughnut_cooked'

def test_doughnut_fryer_cannot_retrieve_before_finished(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    level.tick()
    level.interact(device)
    assert device.is_running
    assert level.held_item is None

def test_doughnut_fryer_will_not_take_batter_while_running(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    assert level.held_item.name == 'doughnut_uncooked'

def test_doughnut_fryer_cannot_take_doughnut(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    original_item = item.DoughnutCooked(level)
    level.held_item = original_item
    level.interact(device)
    assert level.held_item is original_item
    assert level.held_item.name == 'doughnut_cooked'
    assert not device.is_running

def test_doughnut_fryer_duration(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    for _ in range(device.duration_ticks - 1):
        level.tick()
    assert not device.is_finished
    level.tick()
    assert device.is_finished


def test_doughnut_fryer_duration_is_10_seconds(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert device.is_finished

def test_customer_added(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.DoughnutCooked(level)))
    assert len(level.customers) == 1

def test_customer_added_with_one_item_order(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.DoughnutCooked(level)))
    assert len(level.customers[0].order.items) == 1

def test_customer_serve_right_item(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.DoughnutCooked(level)))
    level.held_item = item.DoughnutCooked(level)
    level.interact(level.customers[0])
    assert len(level.customers[0].order.items) == 0
    level.tick()
    assert level.happy_customer == 1 and level.sad_customer == 0

def test_customer_serve_wrong_item(level):
    from applib.model.level import Customer, Order
    customer = Customer(level, Order(item.DoughnutCooked(level)))
    level.held_item = item.DoughnutUncooked(level)
    level.interact(level.customers[0])
    assert len(level.customers[0].order.items) == 1
    level.tick()
    assert level.happy_customer == 0 and level.sad_customer == 0

def test_plate_recipes(level):
    device = level.get_device('station_plate')
    level.held_item = item.DoughnutGlazed(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.DoughnutGlazed)
    level.held_item = item.Sprinkles(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.DoughnutSprinkles)
    level.interact(device)
    assert isinstance(level.held_item, item.DoughnutSprinkles)
    assert device.current_item is None

def test_bin(level):
    device = level.get_device('station_bin')
    level.tick()
    level.held_item = item.DoughnutCooked(level)
    assert isinstance(level.held_item, item.DoughnutCooked)
    level.interact(device)
    assert level.held_item is None
    level.held_item = item.DoughnutCooked(level)
    level.interact(device)
    assert level.held_item is None
    level.interact(device)
    assert level.held_item is None
    assert device.current_item is None

def test_bin_destroys_items(level):
    device = level.get_device('station_bin')
    test_item = item.DoughnutCooked(level)
    assert test_item.level is level
    assert test_item in level.entities
    level.held_item = test_item
    level.interact(device)
    assert test_item.level is None
    assert test_item not in level.entities

def test_customer_arrival_and_leave(level):
    # this test depends on the customer default patience
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 1
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 2
    for _ in range(int(20 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 1
    for _ in range(int(5 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 0
    assert level.sad_customer == 2
    assert level.score == 80

def test_customer_served(level):
    for _ in range(int(5 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 1
    level.held_item = item.DoughnutCooked(level)
    level.interact(level.customers[0])
    level.tick()
    assert len(level.customers) == 0
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 1
    for _ in range(int(50 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 0
    assert level.sad_customer == 1
    assert level.happy_customer == 1
    assert level.score == 40

def test_plate_destroys_previous_item(level):
    plate = level.get_device('station_plate')
    doughnut = item.DoughnutGlazed(level)
    sprinkles = item.Sprinkles(level)
    assert doughnut.level is level
    assert doughnut in level.entities
    assert sprinkles.level is level
    assert sprinkles in level.entities
    level.held_item = doughnut
    level.interact(plate)
    level.held_item = sprinkles
    level.interact(plate)
    assert doughnut.level is None
    assert doughnut not in level.entities
    assert sprinkles.level is None
    assert sprinkles not in level.entities

def test_plates_are_not_weird(level):
    station_dough = level.get_device('station_dough')
    station_plate = level.get_device('station_plate')
    assert level.held_item is None
    assert station_plate.current_item is None
    level.interact(station_dough)
    assert isinstance(level.held_item, item.DoughnutUncooked)
    assert station_plate.current_item is None
    level.interact(station_plate)
    assert level.held_item is None
    assert isinstance(station_plate.current_item, item.DoughnutUncooked)
    level.interact(station_dough)
    assert isinstance(level.held_item, item.DoughnutUncooked)
    assert isinstance(station_plate.current_item, item.DoughnutUncooked)
    level.interact(station_plate)
    assert isinstance(level.held_item, item.DoughnutUncooked)
    assert isinstance(station_plate.current_item, item.DoughnutUncooked)
    

def test_giving_a_customer_their_order_destroys_order_items(level):
    from applib.model.level import Customer, Order
    order_item = item.DoughnutCooked(level)
    made_item = item.DoughnutCooked(level)
    customer = Customer(level, Order(order_item))
    level.held_item = made_item
    level.interact(customer)
    assert order_item.level is None
    assert order_item not in level.entities
    assert made_item.level is None
    assert made_item not in level.entities
