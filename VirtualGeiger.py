import sounddevice as sd
import time
import math
import random
import tkinter
import numpy

class AppState:
    def __init__(self,master):
        self.master = master
        self.numClicks = 0
        self.defaultOutput = "-none-"
        self.output = tkinter.StringVar(master, self.defaultOutput)
        self.stream = None
        self.samplerate = None
        self.channels = None
        self.data, self.fs = sf.read("click.wav", dtype='float32')
        self.len = len(self.data)
        
    def findDevices(self):
        # Build the option list of possible outputs
        devices = sd.query_devices()
        outputs = [self.defaultOutput]
        # Check if it is output MME
        for device in devices:
            if device['max_output_channels'] != 0:
                outputs.append(device['name'])
        return outputs

    def update(self, newClicks):
        self.numClicks = newClicks
    
    def readClicks(self):
        return self.numClicks
    
    def readOutput(self):
        return self.output
    
    def makeClick(self):
        return self.data, self.fs, self.len
    
    def getStream(self):
        return self.stream
    
    def setStream(self,value):
        if self.stream != None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        if value == self.defaultOutput: return
        
        outChannel = sd.query_devices(value)
        self.samplerate = math.floor(outChannel['default_samplerate'])
        self.channels = int(outChannel['max_output_channels'])
        self.stream = sd.OutputStream(device = self.output.get(), latency = 'low')
        self.stream.start()
    
    def buildOutputMenu(self,base):
        return tkinter.OptionMenu(base, self.output, *self.findDevices(), command = lambda x: self.setStream(x))
        
def clickLoop(master,appState,locations):    
    outChannelName = appState.readOutput().get()
    stream = appState.getStream()
    
    CPM = math.floor(float(appState.readClicks()))
    
    if stream == None or CPM == 0: 
        master.after(1000,lambda: clickLoop(master,appState,locations))
        return
    
    samplerate = appState.samplerate
    numChannels = appState.channels
    
    # Probability of starting a click in a frame
    probability = (CPM / 60.0) / samplerate
    
    # Number of frames to iterate
    frames = min([stream.write_available, 1.0 * samplerate])
    
    writeBuffer = numpy.array([0.0] * (numChannels * frames), dtype = numpy.float32)
    
    output = numpy.array([0.0] * 1000, dtype = numpy.float32)
    
    data, fs, size = appState.makeClick()
    for x in range(frames): 
        # Every tick of the stream, see if a particle is captured.
        if random.random() < probability:
            locations.append(0)
        
        sum = 0.0
        avg = 0.0
        for i in range(len(locations)):
            loc = locations[i]
            sum += data[loc]
            locations[i] += 1
        if len(locations) > 0:
            avg = sum / len(locations)
        else:
            avg = 0.0
                
        if sum > 1.0: sum = 1.0
        if sum < -1.0: sum = -1.0
        writeBuffer[x] = sum
        if size in locations: locations.remove(size)
    
    stream.write(writeBuffer)
    
    master.after(50,lambda: clickLoop(master,appState,locations))

def updateLoop(clickState, value):
    clickState.update(value)
    
def main():


    devices = sd.query_devices()

    master = tkinter.Tk()
    master.geometry("300x200")
    state = AppState(master)
    
    base = tkinter.Frame(master, width = 500, height = 400)
    base.grid_columnconfigure(0,weight = 1)
    base.grid_columnconfigure(1,weight = 1)
    base.grid_rowconfigure(0,weight = 1)
    base.grid_rowconfigure(1,weight = 1)
    
    menu = state.buildOutputMenu(base)
    label = tkinter.Label(base,text="Output Channel:")
    
    slider = tkinter.Scale(
        base,
        from_ =  0,
        to_ = 40000,
        tickinterval = 4000,
        orient = tkinter.HORIZONTAL,
        command = lambda x: updateLoop(state,x))
    
    nsew = tkinter.N + tkinter.S + tkinter.E + tkinter.W
    base.pack(expand = True, fill='both')
    label.grid(row = 0, column = 0, sticky = "ew")
    menu.grid(row = 0, column = 1, sticky = "ew")
    slider.grid(row = 1, column = 0, columnspan = 2, sticky = "nsew")
    
    # Start the clicking loop
    master.after(300, lambda: clickLoop(master,state,[]))
    
    tkinter.mainloop()
    
if __name__ == '__main__':
    main()
