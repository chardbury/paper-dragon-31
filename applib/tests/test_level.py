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
        (device.Plating, 0.0, 0.0),
        (device.Bin, 0.0, 0.0),
    ]

    customer_specification = [
        (5, 'friend_patches', [item.DoughnutCooked]),
        (15, 'friend_patches', [item.DoughnutCooked, item.DoughnutIcedBlue])
    ]

    customer_spaces_specification = 2

    fail_ratio = 0.5


@pytest.fixture
def level():
    example_level = ExampleLevel()
    return example_level

@pytest.fixture
def slow_level():
    example_level = ExampleLevel()
    example_level.serve_style = 'slow'
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
    for _ in range(device.duration_ticks):
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
    assert not device.is_running
    assert level.held_item.name == 'doughnut_uncooked'

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
    assert device.current_item.name == 'doughnut_cooked'


def test_doughnut_fryer_duration_is_10_seconds(level):
    device = level.get_device('station_cooking')
    for _ in range(1000):
        level.tick()
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    for _ in range(int(10 // TICK_LENGTH)):
        level.tick()
    assert device.current_item.name == 'doughnut_cooked'

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
    device = level.get_device('station_plating')
    level.held_item = item.Plate(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.Plate)
    assert device.current_item.level is level
    level.held_item = item.DoughnutIcedBlue(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.Plate)
    assert isinstance(device.current_item.holds, item.DoughnutIcedBlue)
    assert device.current_item.level is level
    assert device.current_item.holds.level is level
    level.held_item = item.LadlePurple(level)
    level.interact(device)
    assert level.held_item is None
    assert isinstance(device.current_item, item.Plate)
    assert isinstance(device.current_item.holds, item.DoughnutFinalBluePurple)
    assert device.current_item.level is level
    assert device.current_item.holds.level is level
    level.interact(device)
    assert isinstance(level.held_item, item.Plate)
    assert isinstance(level.held_item.holds, item.DoughnutFinalBluePurple)
    assert level.held_item.level is level
    assert level.held_item.holds.level is level
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

def test_customer_accepts_plated_food(level):
    for _ in range(int(5 // TICK_LENGTH)):
        level.tick()
    assert len(level.customers) == 1
    level.held_item = item.Plate(level)
    level.held_item.holds = item.DoughnutCooked(level)
    level.interact(level.customers[0])
    level.tick()
    assert len(level.customers) == 0


def test_plate_destroys_previous_item(level):
    plate = level.get_device('station_plating')
    doughnut = item.DoughnutIcedBlue(level)
    LadlePurple = item.LadlePurple(level)
    assert doughnut.level is level
    assert doughnut in level.entities
    assert LadlePurple.level is level
    assert LadlePurple in level.entities
    level.held_item = doughnut
    level.interact(plate)
    level.held_item = LadlePurple
    level.interact(plate)
    assert doughnut.level is None
    assert doughnut not in level.entities
    assert LadlePurple.level is None
    assert LadlePurple not in level.entities

def test_plates_are_not_weird(level):
    station_dough = level.get_device('station_dough')
    station_plate = level.get_device('station_plating')
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

def test_fail_level_from_score(level):
    from applib.model.level import Customer, Order
    test = level.has_level_ended()
    assert test is False
    for _ in range(int(36 // TICK_LENGTH)):
        level.tick()
    assert level.fail_score == 40
    assert level.score == 40
    test = level.has_level_ended()
    assert test is True

def test_slow_level_ended_no_customers_leftr(slow_level):
    for _ in range(int(30 // TICK_LENGTH)):
        slow_level.tick()
    slow_level.held_item = item.DoughnutCooked(slow_level)
    slow_level.interact(slow_level.customers[0])
    slow_level.tick()
    for _ in range(int(10 // TICK_LENGTH)):
        slow_level.tick()
    slow_level.held_item = item.DoughnutCooked(slow_level)
    slow_level.interact(slow_level.customers[0])
    slow_level.tick()
    slow_level.held_item = item.DoughnutIcedBlue(slow_level)
    slow_level.interact(slow_level.customers[0])
    slow_level.tick()
    assert slow_level.fail_score == 40
    assert slow_level.score < 40
    assert slow_level.tick_running < slow_level.duration_ticks
    assert slow_level.has_level_ended() is True

def test_ruined_doughnut(level):
    level.held_item = item.DoughnutUncooked(level)
    device = level.get_device('station_cooking')
    level.held_item = item.DoughnutUncooked(level)
    level.interact(device)
    for _ in range(2000):
        level.tick()
    level.interact(device)
    assert level.held_item.name == 'doughnut_burned'
