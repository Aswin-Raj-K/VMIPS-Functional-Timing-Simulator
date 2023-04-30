def runSimulator(iodir):
    # Parse IMEM
    instr = "ADDVV VR3 VR2 VR1\nHALT"
    imem = vp.IMEM(iodir)
    imem.instructions = [instr]
    # Parse SMEM
    sdmem = vp.DMEM("SDMEM", iodir, 13)  # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = vp.DMEM("VDMEM", iodir, 17)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.

    # Create Vector Core
    vcore = vp.Core(imem, sdmem, vdmem)
    result = vcore.run()

    if result == vp.Core.FAILED:  # If core fails
        return vp.Core.FAILED

    # verify here
    vl = vcore.MVL
    v1 = vcore.getRFs("VRF").Read(1)
    v2 = vcore.getRFs("VRF").Read(2)
    v3 = vcore.getRFs("VRF").Read(3)
    for i in range(vl):
        if v1[i] + v2[i] != v3[i]:
            print("Verificaiton Failed for ADDVV")
    print("Verificaiton Done for ADDVV")

    vcore.PC = 0 #reset program counter
    instr = "SUBVV VR3 VR2 VR1\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    if result == vp.Core.FAILED:  # If core fails
        return vp.Core.FAILED
    # verify here
    vl = vcore.MVL
    v1 = vcore.getRFs("VRF").Read(1)
    v2 = vcore.getRFs("VRF").Read(2)
    v3 = vcore.getRFs("VRF").Read(3)
    for i in range(vl):
        if v1[i] - v2[i] != v3[i]:
            print("Verificaiton Failed for SUBVV")
    print("Verificaiton Done for SUBVV")

    #Continue....


    # Dumping the final values
    vcore.dumpRegs(iodir)
    sdmem.dump()
    vdmem.dump()
    return vcore


if __name__ == "__main__":
    iodir = "ISA_Sample"

    print("=========RUNNING SIMULATOR========")
    result = runSimulator(iodir)  # Running simulator
    if result == vp.Core.FAILED:
        exit()

    # Verifying the output
    with open(iodir + '\VDMEMOP.txt', 'r') as file:
        line = file.readlines()[dot_pdt_addr]
        result = int(line.strip())
    print("==================================")

    print("==============RESULT==============")
    if sum == result:  # If dot pdt is same, verification is successfull
        print("Dot pdt is verified and is equal to", result)
    else:
        print("Dot pdt failed!")
    print("==================================")
