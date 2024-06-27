from netpyne import specs, sim

netParams = specs.NetParams()

## Cell types
PYR_HH = {'secs': {}}
PYR_HH['secs']['soma'] = {'geom': {}, 'mechs': {}}                                                    # soma params dict
PYR_HH['secs']['soma']['geom'] = {'diam': 18.8, 'L': 18.8, 'Ra': 123.0}                               # soma geometry
PYR_HH['secs']['soma']['mechs']['hh'] = {'gnabar': 0.12, 'gkbar': 0.036, 'gl': 0.003, 'el': -70}      # soma hh mechanisms
PYR_HH['secs']['dend'] = {'geom': {}, 'topol': {}, 'mechs': {}}                                       # dend params dict
PYR_HH['secs']['dend']['geom'] = {'diam': 5.0, 'L': 150.0, 'Ra': 150.0, 'cm': 1}                      # dend geometry
PYR_HH['secs']['dend']['topol'] = {'parentSec': 'soma', 'parentX': 1.0, 'childX': 0}                  # dend topology
PYR_HH['secs']['dend']['mechs']['pas'] = {'g': 0.0000357, 'e': -70}                                   # dend mechanisms
netParams.cellParams['PYR'] = PYR_HH     

## Population parameters
netParams.popParams['S'] = {'cellType': 'PYR', 'numCells': 5}

## Synaptic mechanism parameters
netParams.synMechParams['exc'] = {'mod': 'Exp2Syn', 'tau1': 0.1, 'tau2': 5.0, 'e': 0}  # excitatory synaptic mechanism

# Stimulation parameters
netParams.stimSourceParams['IStim'] = {'type': 'NetStim', 'rate': 1, 'noise': 0.1}
netParams.stimTargetParams['IStim->first'] = {'source': 'IStim', 'conds': {'cellType': 'PYR'}, 'weight': 0.08, 'delay': 1, 'synMech': 'exc'} #NetCon in NEURON

netParams.connParams['S->S_next'] = {
    'preConds': {'pop': 'S'}, 
    'postConds': {'pop': 'S'},
    'connList': [(i, (i+1)%5) for i in range(5)],  # Connect each neuron to the next, with wraparound
    'weight': 0.08,  # synaptic weight
    'delay': 5,  # transmission delay (ms)
    'synMech': 'exc',  # synaptic mechanism
    'sec': 'dend',              # section to connect to
    'loc': 1.0,                 # location in section to connect to
}

# Simulation options
simConfig = specs.SimConfig()       # object of class SimConfig to store simulation configuration

simConfig.duration = 1*1e3          # Duration of the simulation, in ms
simConfig.dt = 0.025                # Internal integration timestep to use
simConfig.verbose = False           # Show detailed messages
simConfig.recordTraces = {'V_soma':{'sec':'soma','loc':0.5,'var':'v'}}  # Dict with traces to record
simConfig.recordStep = 0.1          # Step size in ms to save data (e.g. V traces, LFP, etc)
simConfig.filename = 'ring_raw'         # Set file output name
simConfig.saveJson = True        # Save params, network and sim output to pickle file

simConfig.analysis['plotRaster'] = {'saveFig': True}                  # Plot a raster
simConfig.analysis['plotTraces'] = {'include': [0], 'saveFig': True}  # Plot recorded traces for this list of cells
# Note that any cells specified in the include parameter of simConfig.analysis['plotTraces'] are automatically added to recordCells for convenience
simConfig.analysis['plot2Dnet'] = {'saveFig': True}                   # plot 2D cell positions and connections

sim.createSimulateAnalyze(netParams, simConfig)

for key, value in sim.simData.items():
    print(f"Key: {key}")
    print(f"Type: {type(value)}")
    print(f"Shape (if applicable): {getattr(value, 'shape', 'N/A')}")
    print("---")

print(list(sim.simData['spkt']))  # spike times
print(list(sim.simData['spkid']))  # spike cell IDs