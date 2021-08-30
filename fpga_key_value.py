#!/usr/bin/env python3
from migen import *
import random

WIDTH = 16 # How many bits can be in key and value
DEPTH = 9 # How many bits for the storage location
CAPACITY = 2**DEPTH # Capacity of key_value store


class key_value(Module):
    def __init__(self, width, depth):

        #inputs:
        self.KEY_i = KEY_i = Signal(width)
        self.VALUE_i_o = VALUE_i_o = Signal(width)
        self.RESET_i = RESET_i = Signal() #active for returing back to the retset state
        self.ADR_i = ADR_i = Signal(depth)
        self.DAT_i = DAT_i = Signal(width)
        self.WE_i = WE_i = Signal() #write enable
        self.STB_i = STB_i = Signal() #active to indicate bus transaction request
        self.CYC_i = CYC_i  = Signal() #wishbone transaction, true on (or before) the first i_wb_stb clock, stays true until the last o_wb_ack

        #outputs
        self.STALL_o = STALL_o = Signal() # false when the transaction happens
        self.ACK_o = ACK_o = Signal() #active for indicating the end of the transaction
        self.DAT_o = DAT_o = Signal(width)

        #imported_modules
        fsm = FSM(reset_state="RESET")
        self.submodules += fsm

        storage = Memory(width, depth)
        self.specials += storage

        ###

        #internal signals
        write_port = storage.get_port(write_capable = True)
        read_port = storage.get_port(has_re=True)

        ###

        self.comb += [
            write_port.adr.eq(ADR_i),
            read_port.adr.eq(ADR_i),
            write_port.dat_w.eq(DAT_i),
            DAT_o.eq(write_port.dat_r)
        ]

        fsm.act("INACTIVE",

            NextValue(ADR_i,KEY_i),
            STALL_o.eq(1),
            NextValue(ACK_o,0),
            If((STB_i == 1) ,
                NextState("READING")),
            If((STB_i == 1) & (WE_i == 1),
                NextState("WRITING"))
        )

        fsm.act("READING",
            NextValue(STALL_o,0),
            NextValue(read_port.re,1),

            If((RESET_i == 1),
                NextState("RESET")
            ),

            If((CYC_i == 0),
                NextValue(read_port.re,0),
                NextValue(ACK_o,1),
                NextState("INACTIVE"),
            )

        )


        fsm.act("WRITING",
            STALL_o.eq(0),
            NextValue(write_port.we,1),

            If((RESET_i == 1),
                NextState("RESET")
            ),

            If((CYC_i == 0),
                NextValue(write_port.we,0),
                NextValue(ACK_o,1),
                NextState("INACTIVE")
            )

        )

        fsm.act("RESET",
                NextState("INACTIVE")
        )

def tick():
    global t
    t=t+1
    yield

# utility test functions

def store_key_value(dut,key,value):
    # do whatever is necessary to store key/value

    yield dut.VALUE_i_o.eq(value)
    yield dut.KEY_i.eq(key)
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    yield
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield from tick()
    yield dut.CYC_i.eq(0)
    yield from tick()

    MAX_WAIT_CYCLES=50
    for i in range(MAX_WAIT_CYCLES):
        if ((yield dut.STALL_o) ==1):
            # ok, we got the data
            break
        else:
            # otherwise, wait another clock cycle
            yield from tick()

    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting to get data")

    if (yield dut.ADR_i == 512):   # FIXME: what is the signal  ----fixed
        raise ValueError("Capacity is full")

    stored_location = (yield dut.ADR_i)
    return stored_location

def recall_from_key(dut,key):

    yield dut.CYC_i.eq(1)
    yield dut.STB_i.eq(1)
    yield dut.KEY_i.eq(key)
    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield dut.CYC_i.eq(0)
    yield from tick()

    MAX_WAIT_CYCLES=50
    for i in range(MAX_WAIT_CYCLES):
        if ((yield dut.STALL_o) ==1):
            # ok, we got the data
            break
        else:
            # otherwise, wait another clock cycle
            yield from tick()

    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting to get data")

    return (yield dut.VALUE_i_o)


def recall_from_location(dut,location):

    yield dut.CYC_i.eq(1)
    yield dut.STB_i.eq(1)
    yield dut.ADR_i.eq(location)
    yield from tick()
    yield dut.STB_i.eq(0)
    yield from tick()
    yield dut.CYC_i.eq(0)
    yield from tick()

    MAX_WAIT_CYCLES=50
    for i in range(MAX_WAIT_CYCLES):
        if ((yield dut.STALL_o) ==1):
            # ok, we got the data
            break
        else:
            # otherwise, wait another clock cycle
            yield from tick()

    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting to get data")


    return (yield dut.VALUE_i_o)

def simulation_story(dut):

    global t
    t = 0
    # if it needs it, here is some empty startup time
    for i in range(5):
        yield from tick()

    capacity_left = CAPACITY
    stored_keys_values = {}
    stored_locations = {}
    
    temp = {stored_location : key for key, stored_location in stored_locations.items()}
    res = {stored_location : key for key, stored_location in temp.items()}
    res = {}

    for key,stored_location in stored_locations.items():
        if value not in res.values():
             res[key] = stored_location



    # Tests for issue #115 ---

    key=1111
    value=11111
    stored_location = yield from store_key_value(dut,1111,11111)
    res[key] = stored_location
    assert (value == (yield from recall_from_location(dut,stored_location)))
    capacity_left = capacity_left-1

    key=2222
    value=22222
    stored_location = yield from store_key_value(dut,key,value)
    res[key] = stored_location
    assert (value == (yield from recall_from_location(dut,stored_location)))
    capacity_left = capacity_left-1

    key=3334
    value=33334
    stored_location = yield from store_key_value(dut,key,value)
    res[key] = stored_location
    assert (value == (yield from recall_from_location(dut,stored_location)))
    capacity_left = capacity_left-1

    # Test to see if we can write a new value for a key
    key=1111
    value=10101
    stored_location = yield from store_key_value(dut,key,value)
    res[key] = stored_location
    assert (value == (yield from recall_from_location(dut,stored_location)))

    # Test to see if KEYS are not used as locations.
    # How does this test work?
    # Since the keyspace is larger than the capacity_left,
    # we generate two keys that will map to the same location
    # by throwing away bits.
    
    key1=0x1445
    value1=7878
    stored_location1 = yield from store_key_value(dut,key1,value1)
    res[key1] = stored_location1
    capacity_left = capacity_left-1
    assert (value1 == (yield from recall_from_location(dut,stored_location1)))



    # throw away bit from beginning
    key2=0x0445
    value2=7979
    stored_location2 = yield from store_key_value(dut,key2,value2)
    res[key2] = stored_location2
    capacity_left = capacity_left-1
    assert (value2 == (yield from recall_from_location(dut,stored_location2)))

    # throw away bit from end

    key3=0x1444
    value3=7676
    stored_location3 = yield from store_key_value(dut,key3,value3)
    res[key3] = stored_location3
    capacity_left = capacity_left-1
    assert (value3 == (yield from recall_from_location(dut,stored_location3)))
    
    # Lets make sure they are not stored in the same location
    assert(stored_location1 != stored_location2)
    assert(stored_location1 != stored_location3)
    assert(stored_location3 != stored_location2)

    # Lets make sure we can still get all our numbers back
    assert (value1 == (yield from recall_from_location(dut,stored_location1)))
    assert (value2 == (yield from recall_from_location(dut,stored_location2)))
    assert (value3 == (yield from recall_from_location(dut,stored_location3)))

    key=1111
    value=10010
    stored_location = yield from store_key_value(dut,key,value)
    res[key] = stored_location
    capacity_left = capacity_left-1
    assert (value == (yield from recall_from_location(dut,stored_location)))

    # uses a new location

    # Lets fill some random key values, and check them by location
    for j in range(int(capacity_left/2)):

    # Tests for issue #1width __


    # Lets store values with random keys, until half capacity_left
        # generate a random key and make sure we havent already used it
        while key in stored_keys_values:
            key = random.getrandbits(WIDTH)

        random_value = random.getrandbits(WIDTH)
        stored_location = yield from store_key_value(dut,key,random_value)
        res[key] = stored_location
        stored_keys_values[key] = random_value
        capacity_left = capacity_left - 1

    # Now lets recall all the values by the location and see
    # if it returns the correct numbers

    for (check_key,check_location) in sorted(stored_locations.items()):
        print(f"Checking {check_key} is it in location {check_location}")
        check_value = stored_keys_values[key]
        assert (check_value == (yield from recall_from_location(dut,check_location)))


    capacity_left = capacity_left - 3 # because we already used 3 locations in test above

    key = 1111
    for j in range(capacity_left):

        # generate a random key and make sure we havent already used it
        while key in stored_keys_values:
            key = random.getrandbits(WIDTH)

        random_value = random.getrandbits(WIDTH)
        yield from store_key_value(dut,key,random_value)
        stored_keys_values[key] = random_value

    # Now lets recall all the values by the keys and see
    # if it returns the correct numbers

    for (check_key,check_value) in sorted(stored_keys_values.items()):
        print(f"Checking {check_key} does it have {check_value}")
        assert (check_value == (yield from recall_from_key(dut,check_key)))


    # TODO: write test to make sure an error is returned

    random_value = random.getrandbits(WIDTH)
    try:
        stored_location = yield from store_key_value(dut,key,random_value)
        raise("The store operation did not give exception, but we expected an error")
    except Error as the_error:
        print("Ok, got an error as expected")

if __name__ == "__main__":
    dut = key_value(width=WIDTH, depth=DEPTH)
    run_simulation(dut, simulation_story(dut), vcd_name="test_key_value_memory_wb_.vcd")
