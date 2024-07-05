from netpyne import specs, sim
import matplotlib.pyplot as plt
import numpy as np
from neuron import h
h.load_file('stdrun.hoc')

def generate_pulse_packet(n_spikes, t_mean, t_stdvar, seed=None):
    if seed is not None:
        np.random.seed(seed)
    return np.random.normal(t_mean, t_stdvar, n_spikes)

def run_single_packet(a_in, s_in):
    # Network parameters
    netParams = specs.NetParams()     # object of class NetParams to store the network parameters

    ## Cell types
    secs = {} # sections dict
    secs['soma'] = {'geom': {}, 'mechs': {}}                                                # soma params dict
    secs['soma']['geom'] = {'diam': 15, 'L': 14, 'Ra': 120.0}                               # soma geometry
    secs['soma']['mechs']['hh'] = {'gnabar': 0.13, 'gkbar': 0.036, 'gl': 0.003, 'el': -70}  # soma hh mechanism
    netParams.cellParams['E'] = {'secs': secs}                                              # add dict to list of cell params

    ## Population parameters
    netParams.popParams['Neuron'] = {'cellType': 'E', 'numCells': 1}

    ## Synaptic mechanism parameters
    netParams.synMechParams['exc'] = {'mod': 'Exp2Syn', 'tau1': 0.8, 'tau2': 5.3, 'e': 0}  # NMDA synaptic mechanism

    # Stimulation parameters
    pulse_packet_times = generate_pulse_packet(n_spikes=a_in, t_mean=20, t_stdvar=s_in, seed=None)
    pulse_packet_times = np.sort(np.round(pulse_packet_times, 1))
    pulse_packet_times = pulse_packet_times[(pulse_packet_times >= 0) & (pulse_packet_times <= 100)]
    pulse_packet_times = pulse_packet_times.tolist()

    # Create IClamp sources for each spike in the pulse packet
    for i, spike_time in enumerate(pulse_packet_times):
        netParams.stimSourceParams[f'IClamp_{i}'] = {
            'type': 'IClamp',
            'del': spike_time,  # delay before onset of current
            'dur': 0.1,  # duration of current injection (short to mimic a spike)
            'amp': 0.4  # amplitude of current injection
        }
        
        # Connect each IClamp to target neurons
        netParams.stimTargetParams[f'IClamp_{i}->targetNeurons'] = {
            'source': f'IClamp_{i}',
            'conds': {'pop': 'Neuron'},  # Specify the target population
            'sec': 'soma',
            'loc': 0.5
        }

    # Simulation options
    simConfig = specs.SimConfig()        # object of class SimConfig to store simulation configuration

    simConfig.duration = 100           # Duration of the simulation, in ms
    simConfig.dt = 0.05                  # Internal integration timestep to use
    simConfig.verbose = False            # Show detailed messages
    simConfig.recordTraces = {'V_soma':{'sec':'soma','loc':0.5,'var':'v'}}  # Dict with traces to record
    simConfig.recordStep = 0.5             # Step size in ms to save data (e.g. V traces, LFP, etc)
    simConfig.filename = 'fig2'          # Set file output name
    simConfig.savePickle = False         # Save params, network and sim output to pickle file

    # simConfig.analysis['plotRaster'] = {'orderBy': 'y', 'orderInverse': True, 'saveFig': True}         # Plot a raster

    # Create network and run simulation
    sim.create(netParams = netParams, simConfig = simConfig)

    # noise stimulation
    i_noise_list = []
    for cell in sim.net.cells:
        i_noise = h.INoise(cell.secs['soma']['hObj'](0.5))
        i_noise.delay = 0
        i_noise.dur = simConfig.duration
        i_noise.std = 0.45
        # i_noise.seed(cell.gid)
        i_noise_list.append(i_noise)

    sim.runSim()                          # run parallel Neuron simulation
    sim.gatherData()                      # gather spiking data and cell info from each node
    sim.saveData()                        # save params, cell info and sim output to file (pickle,mat,txt,etc)
    # sim.analysis.plotData()               # plot spike raster

    if sim.allSimData['spkt'] == []:
        return 0
    else:
        spike_time_one = 0
        for spike_time in sim.allSimData['spkt']:
            if (spike_time <= 30 and spike_time >= 10):
                spike_time_one = spike_time
                break
        return spike_time_one