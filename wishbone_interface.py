from migen import *

class wb_interface(Module):
    def __init__(self):


        FirstAdress = Signal(16)
        SecondAdress = Signal(16)
        ThirdAdress = Signal(16)
        FourthAdress = Signal(16)
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
        # self.memory_storage = mem = mem()

        #slave_module

        

        fsm.act("INACTIVE",
            STALL_o.eq(1),
	    NextValue(ACK_o,0),
            If((STB_i == 1) ,
                
                NextState("READING")),
            If((STB_i == 1) & (WE_i == 1),
                
                NextState("WRITING"))
        )

        fsm.act("READING",
            
            STALL_o.eq(0),
            If(ADR_i == 1,
                NextValue(DAT_o,FirstAdress)
            ).Elif(ADR_i == 2,
                 NextValue(DAT_o,SecondAdress)
            ).Elif(ADR_i == 3,
                NextValue(DAT_o,ThirdAdress)
            ).Else(
                NextValue(DAT_o,FourthAdress),
            ),
            

            If((RESET_i == 1),
                NextState("RESET")
            ),


            If((CYC_i == 0),
                NextValue(ACK_o,1),
                NextState("INACTIVE"),
            )


        )

        fsm.act("WRITING",
            STALL_o.eq(0),
            If(ADR_i == 1,
                NextValue(FirstAdress,DAT_i)
            ).Elif(ADR_i == 2,
                 NextValue(SecondAdress,DAT_i)
            ).Elif(ADR_i == 3,
                NextValue(ThirdAdress,DAT_i)
            ).Else(
                NextValue(FourthAdress,DAT_i),
            ),
            	

            If((RESET_i == 1),
                NextState("RESET")
            ),

            If((CYC_i == 0),
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

    for i in range(5):
        yield from tick()

    # writing
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(1)
    yield dut.DAT_i.eq(0x1111)
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

    # waiting for writing





    # store another number in storage 2
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(2)
    yield dut.DAT_i.eq(0x2222)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    
    
    yield
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)
    # waiting for writing
    yield from tick()



    # Reading
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(1)


    yield dut.STB_i.eq(1)
    
    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield from tick()	
    yield dut.CYC_i.eq(0)

    yield from tick()

    print("Red number is ",(yield dut.DAT_o))
    assert( 0x1111 == (yield dut.DAT_o))


   



    # Reading Vol2
    yield dut.CYC_i.eq(1)
    yield dut.ADR_i.eq(2)


    yield dut.STB_i.eq(1)
    
    
    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()

    yield dut.CYC_i.eq(0)

    print("Red number is ",(yield dut.DAT_o))
    assert( 0x2222 == (yield dut.DAT_o))



   


    #writing to the third adress
    yield dut.ADR_i.eq(3)
    yield dut.DAT_i.eq(0x3333)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    yield
    yield from tick()
    yield from tick()

    yield dut.CYC_i.eq(0)

    yield from tick()
    


    yield dut.ADR_i.eq(2)


    yield dut.STB_i.eq(1)
    
    yield dut.CYC_i.eq(1)
    yield
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()

    yield dut.CYC_i.eq(0)


    print("Red number is ",(yield dut.DAT_o))
    assert( 0x2222 == (yield dut.DAT_o))





    
    yield dut.ADR_i.eq(1)
    yield dut.CYC_i.eq(1)

    yield dut.STB_i.eq(1)
    
    
    yield 
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()

    yield dut.CYC_i.eq(0)
    




   # writing to the 4th adress


    
    yield dut.ADR_i.eq(4)
    yield dut.DAT_i.eq(0x4444)
    yield dut.WE_i.eq(1)
    yield dut.STB_i.eq(1)
    
    yield
    yield
    yield dut.CYC_i.eq(1)
    yield dut.WE_i.eq(0)
    yield dut.STB_i.eq(0)
    
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)
    yield from tick()

   #reading the 4th adress

    
    yield dut.ADR_i.eq(4)

    yield dut.STB_i.eq(1)
    yield 
    yield 
    
    yield dut.CYC_i.eq(1)
    yield dut.STB_i.eq(0)
    yield from tick()
    yield from tick()
    yield dut.CYC_i.eq(0)
    
    print("Red number is ",(yield dut.DAT_o))
    assert( 0x4444 == (yield dut.DAT_o))


    print("Simulation finished")
    yield from [None] * 4095
if __name__ == "__main__":
    dut = wb_interface()
    run_simulation(dut, simulation_story(dut), vcd_name="test.vcd")
