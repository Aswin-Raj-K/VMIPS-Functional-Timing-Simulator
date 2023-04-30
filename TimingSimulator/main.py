from ComputeEngine import ComputeEngine
from DataEngine import DataEngine
from Decode import Decode
from Fetch import Fetch
from Status import Status
import time
import os

class Config(object):
    def __init__(self, iodir, fileName = "Config.txt"):
        self.filepath = os.path.abspath(os.path.join(iodir, fileName))
        self.parameters = {}  # dictionary of parameter name: value as strings.
        self.numberOfLanes = None
        self.addPipelineDepth = None
        self.mulPipelineDepth = None
        self.divPipelineDepth = None
        self.dataQueueDepth = None
        self.computeQueueDepth = None
        self.numberOfBanks = None
        self.vectorLoadStorePipelineDepth = None
        try:
            with open(self.filepath, 'r') as conf:
                self.parameters = {line.split('=')[0].strip(): int(line.split('=')[1].split('#')[0].strip()) for line in
                                   conf.readlines() if not (line.startswith('#') or line.strip() == '')}
            print("Config - Parameters loaded from file:", self.filepath)
            print("Config parameters:", self.parameters)
            self.parseParameters()
        except:
            print("Config - ERROR: Couldn't open file in path:", self.filepath)
            raise

    def parseParameters(self):
        if self.parameters["dataQueueDepth"] is not None:
            self.dataQueueDepth = self.parameters["dataQueueDepth"]
        else:
            self.dataQueueDepth = 4
            print("dataQueueDepth not found in " + self.filepath + " taking 4 as default value.")

        self.computeQueueDepth = self.parameters["computeQueueDepth"]
        self.numberOfBanks = self.parameters["vdmNumBanks"]
        self.vectorLoadStorePipelineDepth = self.parameters["vlsPipelineDepth"]
        self.numberOfLanes = self.parameters["numLanes"]
        self.addPipelineDepth = self.parameters["pipelineDepthAdd"]
        self.mulPipelineDepth = self.parameters["pipelineDepthMul"]
        self.divPipelineDepth = self.parameters["pipelineDepthDiv"]


class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16)  # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Data.txt"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [ins.split('#')[0].strip() for ins in insf.readlines() if
                                     not (ins.startswith('#') or ins.strip() == '')]
            print("IMEM - Instructions loaded from file:", self.filepath)
            # print("IMEM - Instructions:", self.instructions)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)
            raise

class Core:
    def __init__(self, config, imem):
        self.config = config
        self.imem = imem
        self.compute = ComputeEngine(self.config.addPipelineDepth, self.config.mulPipelineDepth,
                                     self.config.divPipelineDepth, self.config.numberOfLanes)
        self.data = DataEngine(6, self.config.numberOfBanks, self.config.vectorLoadStorePipelineDepth)
        self.decode = Decode(self.config.computeQueueDepth,self.config.dataQueueDepth, 8, 8, self.compute, self.data)
        self.fetch = Fetch(self.imem.instructions, self.decode)
        self.compute.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.data.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.clk = 1
        self.startTime = None
        self.endTime = None

    def run(self):
        print("Timing Simulation Started")
        self.startTime = time.time()
        while not (self.fetch.getStatus() == Status.COMPLETED and self.decode.isClear()):
            status1, instr = self.fetch.run()
            status2, computeInstr, dataInstr, scalarInstr = self.decode.run(instr)
            self.compute.run(computeInstr, self.fetch.getCurrentVectorLength())
            self.data.run(dataInstr)
            self.clk += 1

        self.endTime = time.time()
        print("Timing Simulation Successful")

    def printResult(self):
        time_difference = self.endTime - self.startTime
        minutes = str(int(time_difference // 60))
        seconds = str(int(time_difference % 60))
        # milliseconds = str(int((time_difference - int(time_difference)) * 1000))
        print("================RESULT================")
        print("Clock Cycles: ", self.clk - 1)
        print("Time Elapsed: ", minutes + "m", seconds + "s")
        print("======================================")

    def dumpResult(self):
        pass


if __name__ == "__main__":
    iodir = "IODir"
    imem = IMEM(iodir)
    config = Config(iodir)
    core = Core(config,imem)
    core.run()
    core.printResult()
    core.dumpResult()