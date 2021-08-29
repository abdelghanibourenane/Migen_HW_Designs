from migen import *
from migen.genlib.fsm import *


def _divisor(freq_in, freq_out, max_ppm=None):
    divisor = freq_in // freq_out # freq_in is the fpga clock freq, freq_out is the protocol used clock freq
    if divisor <= 0:
        raise ArgumentError("output frequency is too high")

    ppm = 1000000 * ((freq_in / divisor) - freq_out) / freq_out 
    if max_ppm is not None and ppm > max_ppm:
        raise ArgumentError("output frequency deviation is too high")

    return divisor


class UART(Module):
    def __init__(self, serial, clk_freq, baud_rate):
        self.rx_data = Signal(8)
        self.rx_ready = Signal() # start bit
        self.rx_ack = Signal() # stop bit
        self.rx_error = Signal() # parity bit 

        self.tx_data = Signal(8)nderstanding Migen UART codes ambiguous parts , issues especially with the yield part as it is the 
      part of   the code that we could   edit to implement the blinking times sending example"
        self.tx_ready = Signal()
        self.tx_ack = Signal()

        divisor = _divisor(freq_in=clk_freq, freq_out=baud_rate, max_ppm=50000) # using the created divisor module to adjust the baude rate of the Rx and Tx , divisor value is the time for which 1 bit is sampled, 

        ###

        rx_counter = Signal(max=divisor) # the counter counts till it reaches divisor value where it indicates that the receiver should now exactly read a bit, sample a bit 
        self.rx_strobe = rx_strobe = Signal() # I think strobe is just used to fastly make an action, this is to ensure that the data is sampled at an accurate time
        #CORRECTION : strobe is just label for the rx end of the counting, so strobe signal is active "1" if and onmy if the counter reaches divisor-1, hence you can use this strobe to tell the reciver for ex to sample a bit
        self.comb += rx_strobe.eq(rx_counter == 0)
        self.sync += \
            If(rx_counter == 0,
                rx_counter.eq(divisor - 1) # when counter equals 0, it is setted to divisor -1 in order to start counting to indicates the next read
            ).Else(
                rx_counter.eq(rx_counter - 1) #otherwise, keeps counting till it reaches divisor value
            )

        self.rx_bitno = rx_bitno = Signal(3) # bitno >> the number of the recieved bits , either 1,2,3,4 , 4 because it a hex value
        self.submodules.rx_fsm = FSM(reset_state="IDLE") # calling the FSM module, and assiging idle as the reset state, idle is the end of the transmission, idle also is an indication that a byte has been already transmitted, so the read or write after the idle state is for a new byte
        self.rx_fsm.act("IDLE",
            If(~serial.rx, # ~serial.rx, after the end of the serial data R or T process 
                NextValue(rx_counter, divisor // 2), # after the end of T or R , count just till the half of the baude rate, hence you will read the first bit which is the start from the  middle and not the margines, then when you count the next time till divisor you will sample the bit number 1 " which is after start " you will sample it in its middle, hence insuring accuracy in sampling the bit,
                NextState("START") # for the first counting it should count just till half of the divisor value in order to ensure that when it reads for the next times the data,it reads starting from the middle of the bit, ensuring accuracy
            )
        )
        self.rx_fsm.act("START",
            If(rx_strobe,
                NextState("DATA") # after start , data is red
            )
        )
        self.rx_fsm.act("DATA",
            If(rx_strobe,
                NextValue(self.rx_data, Cat(self.rx_data[1:8], serial.rx)), # what I have understood is that it assigned to the 8 bit rx_data the serial_rx data the recieved ones, it is where sampling is hapenning
# CORRECTION: Giray has provided an accurate definition: The Cat() function is for concatenation, meaning joining signals together. So Cat(signal1, signal2) will put the signal bits together.  eg: Cat( 0b111, 0b000) will give you 0b111000 . So, let's say s1=Signal(3)  and s2=Signal(4). Then if we say  Cat(s1,s2).eq(0b1110000) will assign 111 to s1 and 0000 to s2.

#In the example, we need to know how many bits phase and self.tick is to understand which bits are assigned to phase, and which bits are assigned to self.tick.
                NextValue(rx_bitno, rx_bitno + 1), # it assigned the values one by one
                If(rx_bitno == 7, # when it reaches the 8 th bit it continues to stop, exactly how the protocol works
                    NextState("STOP")
                )
            )
        ) # the following is to indicate that with stop the transmission is completed
        self.rx_fsm.act("STOP",
            If(rx_strobe,
                If(~serial.rx,
                    NextState("ERROR")# 
                ).Else(
                    NextState("FULL")
                )
            )
        ) # the following is to go for idle state after stop
        self.rx_fsm.act("FULL",
            self.rx_ready.eq(1),
            If(self.rx_ack,
                NextState("IDLE")
            ).Elif(~serial.rx,
                NextState("ERROR")
            )
        )
        self.rx_fsm.act("ERROR",
            self.rx_error.eq(1))

        ###
      # the transmitter is kinda the same but with a latch to store the data that we would transmit
        tx_counter = Signal(max=divisor)
        self.tx_strobe = tx_strobe = Signal()
        self.comb += tx_strobe.eq(tx_counter == 0)
        self.sync += \
            If(tx_counter == 0,
                tx_counter.eq(divisor - 1)
            ).Else(
                tx_counter.eq(tx_counter - 1)
            )

        self.tx_bitno = tx_bitno = Signal(3)
        self.tx_latch = tx_latch = Signal(8)
        self.submodules.tx_fsm = FSM(reset_state="IDLE")
        self.tx_fsm.act("IDLE",
            self.tx_ack.eq(1),
            If(self.tx_ready,
                NextValue(tx_counter, divisor - 1),
                NextValue(tx_latch, self.tx_data),
                NextState("START")
            ).Else(
                NextValue(serial.tx, 1)
            )
        )
        self.tx_fsm.act("START",
            If(self.tx_strobe,
                NextValue(serial.tx, 0),
                NextState("DATA")
            )
        )
        self.tx_fsm.act("DATA",
            If(self.tx_strobe,
                NextValue(serial.tx, tx_latch[0]),
                NextValue(tx_latch, Cat(tx_latch[1:8], 0)),
                NextValue(tx_bitno, tx_bitno + 1),
                If(self.tx_bitno == 7,
                    NextState("STOP")
                )
            )
        )
        self.tx_fsm.act("STOP",
            If(self.tx_strobe,
                NextValue(serial.tx, 1),
                NextState("IDLE")
            )
        )
# I am having problems with fully understanding how the yield is used, apparently it is used to assign the data but also to give a clock cycle but how it is really used comparing to verilog  format is the matter

class _TestPads(Module):
    def __init__(self):
        self.rx = Signal(reset=1)
        self.tx = Signal()


def _test_rx(rx, dut):
    def T():
        yield; yield; yield; yield # 4 clock cycle indication, apparently eah one for sampling 1 bit out of 4 bits 1 hex number, and this is how UART works, transmitting starting from the LSB to MSB of 4 bits hex number
    def B(bit):
        yield rx.eq(bit) # in the B state rx either recives O or 1, and it is used for the indication of Start, parity or stop state, and then import "T" function to do a clock cycle
        yield from T()
    def S(): #start bit
        yield from B(0)# giving B "0" meaning that a start state will be the next state
        assert (yield dut.rx_error) == 0 #ensuring that error state is 0 and not 1 which tells that an error exists, so the program will not proceed
        assert (yield dut.rx_ready) == 0 # make sure that ready state is 0, and the ready state is the start and start by default works only for logic 0
    def D(bit): # data bits
        yield from B(bit) # this is reading the state of Rx, either 0 or 1 to Rx
        assert (yield dut.rx_error) == 0
        assert (yield dut.rx_ready) == 0
    def E(): # end bit 
        yield from B(1) # read if it is one
        assert (yield dut.rx_error) == 0
    def O(bits): 
        yield from S() # read the state of start bit
        for bit in bits: # looping in the 8 Rx bits
            yield from D(bit) # reading the Rx bits one by one
        yield from E() # read the value of E, the end bit
    def A(octet):
        yield from T()
        assert (yield dut.rx_data) == octet # verify if the recived data Rx is 8 bits long " octet= 8b"
        yield dut.rx_ack.eq(1) # if so, rx.data=octet, ack equal one, the data recieved is correct (acknowledge or retry (ACK-NAK).)
        while (yield dut.rx_ready) == 1: yield  
        yield dut.rx_ack.eq(0) # when the ready state is reached,
    def F(): #when F " False state" this loop is used when error is discovered
        yield from T()
        assert (yield dut.rx_error) == 1
        yield rx.eq(1)
        yield dut.cd_sys.rst.eq(1)
        yield
        yield
        yield dut.cd_sys.rst.eq(0)
        yield
        yield
        assert (yield dut.rx_error) == 0

    # bit patterns
    yield from O([1, 0, 1, 0, 1, 0, 1, 0])# apparently there is a mistake here , it is 01010101 istead of 10101010
    yield from A(0x55)
    yield from O([1, 1, 0, 0, 0, 0, 1, 1])
    yield from A(0xC3)
    yield from O([1, 0, 0, 0, 0, 0, 0, 1])
    yield from A(0x81)
    yield from O([1, 0, 1, 0, 0, 1, 0, 1])
    yield from A(0xA5)
    yield from O([1, 1, 1, 1, 1, 1, 1, 1])
    yield from A(0xFF)

    # framing error
    yield from S()
    for bit in [1, 1, 1, 1, 1, 1, 1, 1]:
        yield from D(bit)
    yield from S()
    yield from F()

    # overflow error
    yield from O([1, 1, 1, 1, 1, 1, 1, 1])
    yield from B(0)
    yield from F()


def _test_tx(tx, dut): # tx test code, similar to the rx one
    def Th():
        yield; yield
    def T():
        yield; yield; yield; yield
    def B(bit):
        yield from T()
        assert (yield tx) == bit
    def S(octet):
        assert (yield tx) == 1
        assert (yield dut.tx_ack) == 1
        yield dut.tx_data.eq(octet)
        yield dut.tx_ready.eq(1)
        while (yield tx) == 1: yield
        yield dut.tx_ready.eq(0)
        assert (yield tx) == 0
        assert (yield dut.tx_ack) == 0
        yield from Th()
    def D(bit):
        assert (yield dut.tx_ack) == 0
        yield from B(bit)
    def E():
        assert (yield dut.tx_ack) == 0
        yield from B(1)
        yield from Th()
    def O(octet, bits):
        yield from S(octet)
        for bit in bits:
            yield from D(bit)
        yield from E()

    yield from O(0x55, [1, 0, 1, 0, 1, 0, 1, 0])
    yield from O(0x81, [1, 0, 0, 0, 0, 0, 0, 1])
    yield from O(0xFF, [1, 1, 1, 1, 1, 1, 1, 1])
    yield from O(0x00, [0, 0, 0, 0, 0, 0, 0, 0])


def _test(tx, rx, dut):
    yield from _test_rx(rx, dut)
    yield from _test_tx(tx, dut)


class _LoopbackTest(Module): # the test bench part
    def __init__(self, platform):
        serial = plat.request("serial")
        leds   = Cat([plat.request("user_led") for _ in range(8)]) #assigning the leds of the code which represent 8 bits data to the fpga leds
        debug  = plat.request("debug")

        self.submodules.uart = UART(serial, clk_freq=12000000, baud_rate=9600) #importing uart module with freq parameters

        empty = Signal(reset=1) 
        data = Signal(8)
        rx_strobe = Signal() #count end indication for rx
        tx_strobe = Signal() #count end indication for tx
        self.comb += [
            rx_strobe.eq(self.uart.rx_ready & empty),
            tx_strobe.eq(self.uart.tx_ack & ~empty),
            self.uart.rx_ack.eq(rx_strobe),
            self.uart.tx_data.eq(data),
            self.uart.tx_ready.eq(tx_strobe)
        ]
        self.sync += [
            If(rx_strobe,
                data.eq(self.uart.rx_data),
                empty.eq(0) #if data is already sampled , this indicates that thers is no place to add more data, it is full
            ),
            If(tx_strobe,
                empty.eq(1)
            )
        ]

        self.comb += [
            leds.eq(self.uart.rx_data),
            debug.eq(Cat(
                serial.rx,
                serial.tx,
                self.uart.rx_strobe,
                self.uart.tx_strobe,
                # self.uart.rx_fsm.ongoing("IDLE"),
                # self.uart.rx_fsm.ongoing("START"),
                # self.uart.rx_fsm.ongoing("DATA"),
                # self.uart.rx_fsm.ongoing("STOP"),
                # self.uart.rx_fsm.ongoing("FULL"),
                # self.uart.rx_fsm.ongoing("ERROR"),
                # self.uart.tx_fsm.ongoing("IDLE"),
                # self.uart.tx_fsm.ongoing("START"),
                # self.uart.tx_fsm.ongoing("DATA"),
                # self.uart.tx_fsm.ongoing("STOP"),
            ))
        ]


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "sim":
        pads = _TestPads()
        dut = UART(pads, clk_freq=4800, baud_rate=1200)
        dut.clock_domains.cd_sys = ClockDomain("sys")
        run_simulation(dut, _test(pads.tx, pads.rx, dut), vcd_name="uart.vcd")
    elif sys.argv[1] == "loopback":
        from migen.build.generic_platform import *
        from migen.build.platforms import ice40_hx8k_b_evn

        plat = ice40_hx8k_b_evn.Platform()
        plat.add_extension([
            ("debug", 0, Pins("B16 C16 D16 E16 F16 G16 H16 G15"))
        ])

        plat.build(_LoopbackTest(plat))
        plat.create_programmer().load_bitstream("build/top.bin")
