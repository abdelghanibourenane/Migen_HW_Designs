#!/usr/bin/env python3
from migen import *
from litex.soc.interconnect.csr import *

class Storage(Module):
    def __init__(self):
        # Input signals
        self.store_now_active = store_now_active = Signal()  #  This module reads this to know  when storage is requested.
        self.recall_now_active = recall_now_active = Signal() # This module reads this to know when when recall is requested
        self.where_to_store_or_recall = where_to_store_or_recall = Signal(3)
        self.number_to_store = number_to_store = Signal(16) # This module should use this to know the number to store

        # Output signals
        self.stored = stored = Signal() # This module should set this when storage operation is completed
        self.recalled = recalled = Signal()  # This module should set this when reacll operation is completed
        self.number_recalled = number_recalled = Signal(16) # This module should set this to the value of the number that is recalled

        # Signals internal to this module (names do not start with self dot!)
        number_of_location_one  = Signal(16)
        number_of_location_two = Signal(16)
        number_of_location_three = Signal(16)
        number_of_location_four = Signal(16)

        self.sync += [
            If(self.store_now_active & ~self.recall_now_active, [
                self.stored.eq(1),


                If(self.where_to_store_or_recall == 1, [
                    number_of_location_one.eq(number_to_store)
                ]).Elif(self.where_to_store_or_recall == 2, [
                    number_of_location_two.eq(number_to_store)
                ]).Elif(self.where_to_store_or_recall == 3, [
                    number_of_location_three.eq(number_to_store)
                ]).Else([number_of_location_four.eq(number_to_store),
                ])

            ]).Else([
               self.stored.eq(0)
            ])
        ]
        self.sync += [
            If(self.recall_now_active & ~self.store_now_active, [
                self.recalled.eq(1),

                If(self.where_to_store_or_recall == 1, [
                    number_recalled.eq(number_of_location_one)
                ]).Elif(self.where_to_store_or_recall == 2, [
                    number_recalled.eq(number_of_location_two)
                ]).Elif(self.where_to_store_or_recall == 3, [
                    number_recalled.eq(number_of_location_three)
                ]).Else([number_recalled.eq(number_of_location_four)
                ])
           ]).Else([
               self.recalled.eq(0)
           ])
        ]


def tick():
    global t
    t=t+1
    yield

def simulation_story(dut):

    global t
    t = 0
    # if it needs it, here is some empty startup time
    for i in range(5):
        yield from tick()

    # store a number
    yield dut.where_to_store_or_recall.eq(1)
    yield dut.number_to_store.eq(0x1111)
    yield dut.store_now_active.eq(1)
    yield from tick()

    # wait until storage is done
    for i in range(50):
        if ((yield dut.stored) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not get stored signal")

    yield dut.store_now_active.eq(0)
    yield from tick()

    # Let's wait until, the storage allows for another storage
    # That is until dut.stored is back to zero

    for i in range(50):
        if ((yield dut.stored) == 0):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not see stored signal back to 0")


    # store another number in storage 2
    yield dut.where_to_store_or_recall.eq(2)
    yield dut.number_to_store.eq(0x2222)
    yield dut.store_now_active.eq(1)
    yield from tick()

    # wait until storage is done
    for i in range(50):
        if ((yield dut.stored) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not get stored signal")

    yield dut.store_now_active.eq(0)
    yield from tick()

    # lets get our first number
    yield dut.where_to_store_or_recall.eq(1)
    yield dut.recall_now_active.eq(1)
    yield from tick()

    # Let's wait until, the storage recalls the number
    # That is until dut.recalled is 1

    for i in range(50):
        if ((yield dut.recalled) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not see recalled signal back to 0")

    # Lets make sure the number is the same
    print("Received number is ",(yield dut.number_recalled))
    assert( 0x1111 == (yield dut.number_recalled))

    yield dut.recall_now_active.eq(0)
    yield from tick()

    # lets get our second number
    yield dut.where_to_store_or_recall.eq(2)
    yield dut.recall_now_active.eq(1)
    yield from tick()
    # ...

    # wait until recalled
    for i in range(50):
        if ((yield dut.recalled) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not see recalledsignal back to 0")

    # assert number is 0x222
    print("Received number is ",(yield dut.number_recalled))
    assert( 0x2222 == (yield dut.number_recalled))

    yield dut.recall_now_active.eq(0)
    yield from tick()
    # store another number in location 1
    #
    yield dut.where_to_store_or_recall.eq(1)
    yield dut.number_to_store.eq(0x3333)
    yield dut.store_now_active.eq(1)
    yield from tick()



    # wait until stored
    for i in range(50):
        if ((yield dut.stored) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not get stored signal")

    yield dut.store_now_active.eq(0)
    yield from tick()

    # lets get our second number again, to make sure it is still there
    yield dut.where_to_store_or_recall.eq(2)
    yield dut.recall_now_active.eq(1)
    yield from tick()
    # ...

    # wait until recalled
    for i in range(50):
        if ((yield dut.recalled) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not see recalledsignal back to 0")

    # assert number is 0x222
    print("Received number is ",(yield dut.number_recalled))
    assert( 0x2222 == (yield dut.number_recalled))

    yield dut.recall_now_active.eq(0)
    yield from tick()


    # get number in location 1
    yield dut.where_to_store_or_recall.eq(1)
    yield dut.recall_now_active.eq(1)
    yield from tick()

    # wait until recalled
    for i in range(50):
        if ((yield dut.recalled) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not see recalledsignal back to 0")

    # make sure it is now 0x3333
    print("Received number is ",(yield dut.number_recalled))
    assert( 0x3333 == (yield dut.number_recalled))

    yield dut.recall_now_active.eq(0)
    yield from tick()

    # store a number in location 4
    #
    yield dut.where_to_store_or_recall.eq(4)
    yield dut.number_to_store.eq(0x4567)
    yield dut.store_now_active.eq(1)
    yield from tick()

    # wait until stored
    for i in range(50):
        if ((yield dut.stored) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not get stored signal")

    yield dut.store_now_active.eq(0)
    yield from tick()

    # get number in location 4
    yield dut.where_to_store_or_recall.eq(4)
    yield dut.recall_now_active.eq(1)
    yield from tick()

    # wait until recalled
    for i in range(50):
        if ((yield dut.recalled) == 1):
            break
        yield from tick()
    if i>=49:
        raise Exception("Error, did not see recalledsignal back to 0")

    # make sure it is now 0x4567
    print("Received number is ",(yield dut.number_recalled))
    assert( 0x4567 == (yield dut.number_recalled))

    print("Simulation finished")
    yield from [None] * 4095
if __name__ == "__main__":
    dut = Storage()
    run_simulation(dut, simulation_story(dut), vcd_name="test.vcd")
