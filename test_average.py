#!/usr/bin/env python3
from migen import *
from storage_location import Storage
from migen.genlib.divider import Divider
from migen.genlib.fsm import FSM
class Calculator(Module):
    def __init__(self):

        # Inputs
        self.storage_location = Signal(3) # This module reads this to know where number should be stored or recalled.
        self.store_now_active = Signal()  #  This module reads this to know  when storage is requested.
        self.recall_now_active = Signal() # This module reads this to know when when recall is requested
        self.number_to_store = Signal(8) # This module should use this to know the number to store

        self.calculate_now_active = Signal() #  This module reads thisto know when calcuation is requested

        self.number_of_values = Signal(8)


        # Internal Signals
        total_number = Signal(8)
        number_recalled_internal = Signal(8)
        counter = Signal(8)

        start_division = Signal()
        division_finished = Signal()
        result = Signal(8)
        leftover = Signal(8)
        dividing = Signal()

        # Outputs
        self.stored = stored = Signal() # This module should set this when storage operation is completed
        self.recalled = Signal()  # This module should set this when reacll operation is completed
        self.calculated = Signal()  # This module should set this when calulate operation is completed

        self.number_recalled = Signal(8) # This module should set this to the value of the number that is recalled

        # Submodules
        self.submodules.storage = storage = Storage()
        self.submodules.divider = divider = Divider(8)

        fsm = FSM(reset_state="RESET")
        self.submodules += fsm

        fsm.act("RESET",
                NextState("INACTIVE")
        )

        fsm.act("INACTIVE",
            NextValue(self.stored,0),
            NextValue(self.recalled,0),
            NextValue(self.calculated,0),
            NextValue(divider.start_i,0),
            If((self.store_now_active == 1) & (self.recall_now_active == 0),
               self.storage.store_now_active.eq(1),
               self.storage.recall_now_active.eq(0),
               self.storage.where_to_store_or_recall.eq(self.storage_location),
               self.storage.number_to_store.eq(self.number_to_store),
               NextState("storing")
            ).Elif((self.recall_now_active == 1) & (self.store_now_active == 0),
               NextState("recalling"),
               self.storage.recall_now_active.eq(1),
               self.recalled.eq(0),
               self.storage.store_now_active.eq(0),
               self.storage.where_to_store_or_recall.eq(self.storage_location),
            ).Elif((self.calculate_now_active == 1),
                self.storage.store_now_active.eq(0),
                NextValue(total_number,0),
                NextState("calculating")
            )
        )

        #calculation
        #addition, assuming recall is done in one cycle!
        fsm.act("calculating",
                NextValue(counter,1),
                NextValue(self.storage.recall_now_active,1),
                NextState("summing"),
            ),

        fsm.act("summing",
                If(self.storage.recalled == 0,
                       NextValue(self.storage.recall_now_active,1),
                       NextValue(self.storage.store_now_active,0),
                       NextValue(self.storage.where_to_store_or_recall,1),
                       NextValue(counter,counter+1),
                ).Elif((counter < self.number_of_values),
                   If (self.storage.recalled==1,
                       number_recalled_internal.eq(self.storage.number_recalled),
                       NextValue(total_number,total_number + number_recalled_internal),
                       NextValue(self.storage.recall_now_active,1),
                   ).Else(
                       number_recalled_internal.eq(0xff),
                       NextValue(self.storage.recall_now_active,1),
                   )

                ).Elif((counter > self.number_of_values),
                       NextValue(self.calculated,0),
                       NextValue(start_division,1),
                       NextValue(dividing,0),
                       NextState("division"),
                )
        )


        #Division
        fsm.act("division",
            NextValue(divider.start_i,1),
            NextValue(divider.dividend_i,total_number),
            NextValue(divider.divisor_i,self.number_of_values),
            NextValue(start_division,0),
            NextState("dividing"),
        )

        fsm.act("dividing",
                NextValue(divider.start_i,0),
                If(self.divider.ready_o & ~divider.start_i,
                   NextState("output_is_ready"),
                   NextValue(result,divider.quotient_o),
                   NextValue(leftover,divider.remainder_o),
               )
        )
        fsm.act("output_is_ready",
            NextValue(division_finished,1),
            NextValue(divider.start_i,0),
            NextValue(dividing,0),
            NextState("storing_result"),
        )

        fsm.act("storing_result",
            self.storage.where_to_store_or_recall.eq(4),
            self.storage.number_to_store.eq(result),
            self.storage.store_now_active.eq(1),
            self.storage.recall_now_active.eq(0),
            If(self.storage.stored,
               NextState("INACTIVE"),
               self.storage.store_now_active.eq(0),
               NextValue(self.calculated,1),
            ),
        )

        #storing
        fsm.act("storing",
            NextValue(self.stored,self.storage.stored),
            If(self.storage.stored == 1,
                self.storage.store_now_active.eq(0),
                NextState("INACTIVE"),
            )
        )

        #recalling
        fsm.act("recalling",
            self.number_recalled.eq(self.storage.number_recalled),
            self.recalled.eq(self.storage.recalled),
            If(self.storage.recalled == 1,
                self.storage.recall_now_active.eq(0),
                NextState("INACTIVE"),
            )
        )

def tick():
    print("tick")
    yield

# Helper functions for simulation
def wait_for(cycles):
    print(f'Waiting for {cycles} cycles')
    for i in range(cycles):
        yield from tick()

def wait_storage_available(dut):
    print(f'Waiting for storage to be available')
    # Wait until the number storage facility is available
    MAX_WAIT_CYCLES=20
    for i in range(MAX_WAIT_CYCLES):
        if ((yield dut.stored == 0) and (yield dut.store_now_active == 0) and
            (yield dut.recalled == 0) and (yield dut.recall_now_active == 0)):
            break
        yield from tick()
    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting for storage to become available")

def wait_calculator_available(dut):
    print(f'Waiting for calculator to be available')
    # Wait until the calculator is available
    MAX_WAIT_CYCLES=20
    for i in range(MAX_WAIT_CYCLES):
        if ((yield dut.calculate_now_active == 0) and (yield dut.calculated == 0)):
            break
        yield from tick()
    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting for calculator to become available")

def calculate(dut):
    yield from wait_calculator_available(dut)
    print(f'Doing calculation')
    yield dut.number_of_values.eq(3) #we have stored 4 tho ; why is it 3; shouldn't this be specified depending on how many numbers we store? k

    yield dut.calculate_now_active.eq(1)

    # Wait until calculation is done
    MAX_WAIT_CYCLES=100
    for i in range(MAX_WAIT_CYCLES):
        if (yield dut.calculated == 1):
            break
        yield from tick()
    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting for calculation to be done")

    yield dut.calculate_now_active.eq(0)
    yield from tick()

def store_number(dut, number_to_store, location):
    yield from wait_storage_available(dut)
    print(f'Storing { number_to_store} in location { location}.')
    # Load a number into storage
    yield dut.number_to_store.eq(number_to_store)
    yield dut.storage_location.eq(location)
    yield dut.store_now_active.eq(1)
    yield from tick()

    # Wait until number is loaded
    MAX_WAIT_CYCLES=10
    for i in range(MAX_WAIT_CYCLES):
        if (yield dut.stored == 1):
            break
        yield from tick()
    if i==(MAX_WAIT_CYCLES-1):
        raise Exception("Timeout waiting for number to be stored")

    yield dut.store_now_active.eq(0)
    yield from tick()

def recall_number(dut,location):
    yield from wait_storage_available(dut)
    print(f'Recalling number in location { location}.')
    # Load a number into storage
    yield dut.storage_location.eq(location)
    yield dut.recall_now_active.eq(1)
    yield from tick()

    # Wait until number is loaded
    MAX_WAIT_CYCLES=10
    for i in range(MAX_WAIT_CYCLES):
        if (yield dut.recalled == 1):
            break
        yield from tick() #the clock wasn't updating as this was not here 
    if i==(MAX_WAIT_CYCLES-1): #was i>=max_wait_cycles 
        raise Exception("Timeout waiting for number to be recalled")

    number_recalled =     yield dut.number_recalled
    print(f'Recalled number in location { location} is { number_recalled }.')

    yield dut.recall_now_active.eq(0)
    yield from tick()

    return (yield dut.number_recalled)

def simulation_story(dut):
    print('Starting simulation')

    # Lets give a few cycles to allow the board to startup
    yield from wait_for(5)

    # Store numbers
    yield from store_number(dut, 5, location=1)
    yield from store_number(dut, 7, location=2)
    yield from store_number(dut, 9, location=4)

    # Try to get the numbers to make sure they are stored
    if ((yield from recall_number(dut, location=1)) != 5):
        raise Exception("stored number in location 1 does not match")

    if ((yield from recall_number(dut, location=2)) != 7):
        raise Exception("stored number in location 2  does not match")

    if ((yield from recall_number(dut, location=4)) != 9):
        raise Exception("stored number in location 4  does not match")
    #why isn't the number of values stated here but rather in caluclate? 

    # Store 3rd number; isn't this the 4th number? 
    yield from store_number(dut, 12, location=3)

    # Calculate average
    yield from calculate(dut)

    # Get the number from location 4 and see if the average is correct
    r = yield from recall_number(dut,location=4)
    if (r != 8):
        raise Exception(f"average is not calculated correctly. Got {r} but was expecting 8")

    print('Simulation ended successfully')

dut = Calculator()
run_simulation(dut, simulation_story(dut), vcd_name="test_average.vcd")
