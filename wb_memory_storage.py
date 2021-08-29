#!/usr/bin/env python3
from migen import *

class Wb_Mem(Module):
    def __init__(self, width, depth):

        #inputs:
        self.RESET_i = RESET_i = Signal() #active for returing back to the retset state
        self.ADR_i = ADR_i = Signal(16)
        self.DAT_i = DAT_i = Signal(16)
        self.WE_i = WE_i = Signal() #write enable
        self.STB_i = STB_i = Signal() #active to indicate bus transaction request
        self.CYC_i = CYC_i  = Signal() #wishbone transaction, true on (or before) the first i_wb_stb clock, stays true until the last o_wb_ack

        #outputs
        self.STALL_o = STALL_o = Signal() # false when the transaction happens
        self.ACK_o = ACK_o = Signal() #active for indicating the end of the transaction
        self.DAT_o = DAT_o = Signal(16)


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

def simulation_story(dut):

    global t
    t = 0
    # if it needs it, here is some empty startup time
    for i in range(5):
        yield from tick()

    # see if storage can handle more than 50 locations
    for i in range (50):
        yield dut.ADR_i.eq(i+20)
        yield dut.DAT_i.eq(i)
        yield dut.CYC_i.eq(1)
        yield dut.WE_i.eq(1)
        yield dut.STB_i.eq(1)
        yield
        yield dut.WE_i.eq(0)
        yield dut.STB_i.eq(0)
        yield
        yield

        yield from tick()

        yield dut.CYC_i.eq(0)
        yield from tick()

        print("stored number is ",(yield dut.DAT_i))
        print("in adress ",(yield dut.ADR_i))
        yield from tick()

    #wriring the first value
    yield dut.ADR_i.eq(100)
    yield dut.DAT_i.eq(0x1000)
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    yield
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield
    yield

    yield from tick()
    yield dut.CYC_i.eq(0)

    print("stored number is ",(yield dut.DAT_i))
    print("in adress ",(yield dut.ADR_i))

    #reading the first value
    yield from tick()
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(100)


    yield dut.STB_i.eq(1)

    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)

    yield from tick()

    print("Red number is ",(yield dut.DAT_o))
    print("of adress: ",(yield dut.ADR_i))
    assert( 0x1000 == (yield dut.DAT_o))

    #wriring the second value
    yield dut.ADR_i.eq(200)
    yield dut.DAT_i.eq(0x2000)
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    yield
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield
    yield

    yield from tick()
    yield dut.CYC_i.eq(0)
    print("stored number is ",(yield dut.DAT_i))
    print("in adress ",(yield dut.ADR_i))

    #reading the second value
    yield from tick()
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(200)

    yield dut.STB_i.eq(1)

    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)

    yield from tick()

    print("Red number is ",(yield dut.DAT_o))
    print("of adress: ",(yield dut.ADR_i))
    assert( 0x2000 == (yield dut.DAT_o))

    #wriring the third value
    yield dut.ADR_i.eq(300)
    yield dut.DAT_i.eq(0x3000)
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    yield
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield
    yield

    yield from tick()
    yield dut.CYC_i.eq(0)
    print("stored number is ",(yield dut.DAT_i))
    print("in adress ",(yield dut.ADR_i))

    #reading the third value
    yield from tick()
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(300)

    yield dut.STB_i.eq(1)

    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)

    yield from tick()

    print("Red number is ",(yield dut.DAT_o))
    print("of adress: ",(yield dut.ADR_i))
    assert( 0x3000 == (yield dut.DAT_o))

    #wriring the fourth value
    yield dut.ADR_i.eq(400)
    yield dut.DAT_i.eq(0x4000)
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    yield
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield
    yield

    yield from tick()
    yield dut.CYC_i.eq(0)
    print("stored number is ",(yield dut.DAT_i))
    print("in adress ",(yield dut.ADR_i))

    #reading the third value
    yield from tick()
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(400)

    yield dut.STB_i.eq(1)
    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)

    yield from tick()

    print("Red number is ",(yield dut.DAT_o))
    print("of adress: ",(yield dut.ADR_i))
    assert( 0x4000 == (yield dut.DAT_o))

if __name__ == "__main__":
    dut = Wb_Mem(16, 16)
    run_simulation(dut, simulation_story(dut), vcd_name="test_memory_wb.vcd")
