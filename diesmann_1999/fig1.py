from netpyne import specs, sim
import numpy as np
from neuron import h
h.load_file('stdrun.hoc')

def sine_wave(t, amplitude, frequency, phase=0):
    return amplitude * np.sin(2 * np.pi * frequency * t + phase)

# Network parameters
netParams = specs.NetParams()     # object of class NetParams to store the network parameters

netParams.sizeX = 100             # x-dimension (horizontal length) size in um
netParams.sizeY = 1000            # y-dimension (vertical height or cortical depth) size in um
netParams.sizeZ = 100             # z-dimension (horizontal length) size in um
netParams.propVelocity = 5.0    # propagation velocity (um/ms)
netParams.probLengthConst = 150.0 # length constant for conn probability (um)

## Cell types
secs = {} # sections dict
secs['soma'] = {'geom': {}, 'mechs': {}}                                                # soma params dict
secs['soma']['geom'] = {'diam': 15, 'L': 14, 'Ra': 120.0}                               # soma geometry
secs['soma']['mechs']['hh'] = {'gnabar': 0.13, 'gkbar': 0.036, 'gl': 0.003, 'el': -70}  # soma hh mechanism
netParams.cellParams['E'] = {'secs': secs}                                              # add dict to list of cell params

## Population parameters
for i in range(10):
    if i == 0:
        netParams.popParams[f'E{i}_in'] = {'cellType': 'E', 'numCells': 55, 'yRange': [i * 100, i * 100 + 1]}
        netParams.popParams[f'E{i}'] = {'cellType': 'E', 'numCells': 45, 'yRange': [i * 100, i * 100 + 1]}
    else:
        netParams.popParams[f'E{i}'] = {'cellType': 'E', 'numCells': 100, 'yRange': [i * 100, i * 100 + 1]}

## Synaptic mechanism parameters
netParams.synMechParams['exc'] = {'mod': 'Exp2Syn', 'tau1': 0.8, 'tau2': 5.3, 'e': 0}  # NMDA synaptic mechanism

# Stimulation parameters
netParams.stimSourceParams['IStim'] = {'type': 'IClamp', 'del': 1, 'dur': 10, 'amp': 0.4}
netParams.stimTargetParams['IStim->S'] = {'source': 'IStim', 'sec':'soma', 'loc': 0.5, 'conds': {'pop':'E0_in'}, 'synMech': 'exc'}

# Spacial connection
for i in range(10):
    if i == 0:
        netParams.connParams[f'E{i}_in->E{i+1}'] = {
        'preConds': { 'pop' : f'E{i}_in' }, 'postConds': { 'pop' : f'E{i+1}' },  #  E -> all (100-1000 um)
        'probability': 0.1 ,                  # probability of connection // CAN CHANGE
        'weight': 0.0007,         # synaptic weight
        'delay': 5,      # transmission delay (ms)
        'synMech': 'exc'}
    else:
        netParams.connParams[f'E{i}->E{i+1}'] = {
        'preConds': { 'pop' : f'E{i}' }, 'postConds': { 'pop' : f'E{i+1}' },  #  E -> all (100-1000 um)
        'probability': 0.1 ,                  # probability of connection // CAN CHANGE
        'weight': 0.0007,         # synaptic weight
        'delay': 5,      # transmission delay (ms)
        'synMech': 'exc'}

# Simulation options
simConfig = specs.SimConfig()        # object of class SimConfig to store simulation configuration

simConfig.duration = 100           # Duration of the simulation, in ms
simConfig.dt = 0.05                  # Internal integration timestep to use
simConfig.verbose = False            # Show detailed messages
simConfig.recordTraces = {'V_soma':{'sec':'soma','loc':0.5,'var':'v'}}  # Dict with traces to record
simConfig.recordStep = 1             # Step size in ms to save data (e.g. V traces, LFP, etc)
simConfig.filename = 'fig1'          # Set file output name
simConfig.savePickle = False         # Save params, network and sim output to pickle file

simConfig.analysis['plotRaster'] = {'orderBy': 'y', 'orderInverse': True, 'saveFig': True}         # Plot a raster
simConfig.analysis['plotTraces'] = {'include': [('E2',0), ('E4', 0), ('E5', 5)], 'saveFig': True}  # Plot recorded traces for this list of cells
simConfig.analysis['plot2Dnet'] = {'saveFig': True}                                                # plot 2D cell positions and connections
simConfig.analysis['plotConn'] = {'saveFig': True}                                                 # plot connectivity matrix

# Create network and run simulation
sim.createSimulateAnalyze(netParams = netParams, simConfig = simConfig)

# noise stimulation
i_noise_list = []
for cell in sim.net.cells:
    i_noise = h.INoise(cell.secs['soma']['hObj'](0.5))
    i_noise.delay = 0
    i_noise.dur = simConfig.duration
    i_noise.std = 0.4
    i_noise.seed(cell.gid)
    i_noise_list.append(i_noise)

sim.runSim()                          # run parallel Neuron simulation
sim.gatherData()                      # gather spiking data and cell info from each node
sim.saveData()                        # save params, cell info and sim output to file (pickle,mat,txt,etc)
sim.analysis.plotData()               # plot spike raster

sim.saveJSON('test.json', sim.allSimData)