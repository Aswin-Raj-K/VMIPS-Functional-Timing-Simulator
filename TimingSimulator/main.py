import argparse
import glob

from computeEngine import ComputeEngine
from dataEngine import DataEngine
from decode import Decode
from fetch import Fetch
from status import Status
import time
import os


class Config(object):
    def __init__(self, iodir, fileName="Config.txt"):
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
    def __init__(self, config, imem, iodir):
        self.config = config
        self.imem = imem
        self.iodir = iodir
        self.compute = ComputeEngine(self.config.addPipelineDepth, self.config.mulPipelineDepth,
                                     self.config.divPipelineDepth, self.config.numberOfLanes)
        self.data = DataEngine(6, self.config.numberOfBanks, self.config.vectorLoadStorePipelineDepth)
        self.decode = Decode(self.config.computeQueueDepth, self.config.dataQueueDepth, 8, 8, self.compute, self.data)
        self.fetch = Fetch(self.imem.instructions, self.decode)
        self.compute.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.data.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.clk = 1
        self.clks = []
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
            # print(self.fetch.addr)

        self.endTime = time.time()
        print("Timing Simulation Successful")

    def printResult(self):
        time_difference = self.endTime - self.startTime
        minutes = str(int(time_difference // 60))
        seconds = str(int(time_difference % 60))
        # milliseconds = str(int((time_difference - int(time_difference)) * 1000))
        self.dataOutput = []

        self.dataOutput.append("================RESULT================")
        self.dataOutput.append("Clock Cycles: " + str(self.clk - 1))
        self.dataOutput.append("Time Elapsed: " + minutes + "m " + seconds + "s")
        self.dataOutput.append("======================================")
        for line in self.dataOutput:
            print(line)

    def dumpResult(self, fileName="Output.txt"):
        filepath = os.path.abspath(os.path.join(iodir, fileName))
        try:
            with open(filepath, 'w') as opf:
                lines = [str(line) + '\n' for line in self.dataOutput]
                opf.writelines(lines)
            print(fileName, "- Dumped output into output file in path:", filepath)
        except:
            print(fileName, "- ERROR: Couldn't open output file in path:", filepath)
        pass


def dumpSummary(iodir, cycles, fileName="Summary.txt"):
    cycles.insert(0,"================SUMMARY================")
    cycles.append("======================================")
    filepath = os.path.abspath(os.path.join(iodir, fileName))
    try:
        with open(filepath, 'w') as opf:
            lines = [str(line) + '\n' for line in cycles]
            opf.writelines(lines)
        print(fileName, "- Dumped summary into output file in path:", filepath)
    except:
        print(fileName, "- ERROR: Couldn't open output file in path:", filepath)
    pass


def readFiles(iodir):
    files = os.listdir(iodir)
    txt_files = [file_name for file_name in files if file_name.startswith("Config") and file_name.endswith(".txt")]
    txt_files.sort(key=lambda file_name: int(file_name[len('Config'):file_name.index('.')]))
    print(txt_files)
    return txt_files


def parseArguments():
    parser = argparse.ArgumentParser(
        description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="IODir2", type=str,
                        help='Path to the folder containing the input files - resolved data')
    args = parser.parse_args()
    return os.path.abspath(args.iodir)

if __name__ == "__main__":
    iodir = parseArguments()
    txt_files = readFiles(iodir)
    imem = IMEM(iodir)
    cycles = []
    for index, fileName in enumerate(txt_files):
        print("==============================")
        print("Running:", fileName)
        config = Config(iodir, fileName)
        core = Core(config, imem, iodir)
        core.run()
        core.printResult()
        core.dumpResult("Output" + str(index) + ".txt")
        print("==============================")
        cycles.append(fileName[:fileName.index(".")] + " " + str(core.clk))
    dumpSummary(iodir, cycles)
