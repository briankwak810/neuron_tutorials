from netpyne import specs, sim
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import DBSCAN
from neuron import h
h.load_file('stdrun.hoc')

def generate_pulse_packet(n_spikes, t_mean, t_stdvar, seed=None):
    if seed is not None:
        np.random.seed(seed)
    return np.random.normal(t_mean, t_stdvar, n_spikes)

def run_single_packet_w(a_in, s_in, initial_spike_a, seed):
    # Network parameters
    t_mean = 20
    netParams = specs.NetParams()     # object of class NetParams to store the network parameters

    ## Cell types
    secs = {} # sections dict
    secs['soma'] = {'geom': {}, 'mechs': {}}                                                # soma params dict
    secs['soma']['geom'] = {'diam': 15, 'L': 14, 'Ra': 120.0}                               # soma geometry
    secs['soma']['mechs']['hh'] = {'gnabar': 0.13, 'gkbar': 0.036, 'gl': 0.003, 'el': -70}  # soma hh mechanism
    netParams.cellParams['E'] = {'secs': secs}                                              # add dict to list of cell params

    ## Population parameters
    netParams.popParams[f'Neuron_0'] = {'cellType': 'E', 'numCells': initial_spike_a, 'yRange': [0, 1]}
    for i in range(1, 10):
        netParams.popParams[f'Neuron_{i}'] = {'cellType': 'E', 'numCells': 100, 'yRange': [i * 100, i * 100 + 1]}

    ## Synaptic mechanism parameters
    netParams.synMechParams['exc'] = {'mod': 'Exp2Syn', 'tau1': 0.8, 'tau2': 5.3, 'e': 0}  # NMDA synaptic mechanism

    # Stimulation parameters
    pulse_packet_times = generate_pulse_packet(n_spikes=a_in, t_mean=t_mean, t_stdvar=s_in, seed=seed)
    pulse_packet_times = np.sort(np.round(pulse_packet_times, 1))
    pulse_packet_times = pulse_packet_times[(pulse_packet_times >= 0) & (pulse_packet_times <= 100)]
    pulse_packet_times = pulse_packet_times.tolist()

    print(pulse_packet_times)

    # Create IClamp sources for each spike in the pulse packet
    for i, spike_time in enumerate(pulse_packet_times):
        netParams.stimSourceParams[f'IClamp_{i}'] = {
            'type': 'IClamp',
            'del': spike_time,  # delay before onset of current
            'dur': 0.5,  # duration of current injection (short to mimic a spike)
            'amp': 0.3  # amplitude of current injection
        }
        
        # Connect each IClamp to target neurons
        netParams.stimTargetParams[f'IClamp_{i}->targetNeurons'] = {
            'source': f'IClamp_{i}',
            'conds': {'pop': 'Neuron_0'},  # Specify the target population
            'sec': 'soma',
            'loc': 0.5
        }
    
    # Spacial connection
    for i in range(10):
        netParams.connParams[f'E{i}->E{i+1}'] = {
        'preConds': { 'pop' : f'Neuron_{i}' }, 'postConds': { 'pop' : f'Neuron_{i+1}' },  #  E -> all (100-1000 um)
        'probability': 0.2 ,                  # probability of connection // CAN CHANGE
        'weight': 0.00065,         # synaptic weight
        'delay': 15,      # transmission delay (ms)
        'synMech': 'exc'}

    # Simulation options
    simConfig = specs.SimConfig()        # object of class SimConfig to store simulation configuration

    simConfig.duration = 200           # Duration of the simulation, in ms
    simConfig.dt = 0.1                  # Internal integration timestep to use
    simConfig.verbose = False            # Show detailed messages
    simConfig.recordTraces = {'V_soma':{'sec':'soma','loc':0.5,'var':'v'}}  # Dict with traces to record
    simConfig.recordStep = 0.5             # Step size in ms to save data (e.g. V traces, LFP, etc)
    simConfig.filename = 'fig3'          # Set file output name
    simConfig.savePickle = False         # Save params, network and sim output to pickle file

    simConfig.analysis['plotRaster'] = {'orderBy': 'y', 'orderInverse': True, 'saveFig': True}         # Plot a raster

    # Create network and run simulation
    sim.create(netParams = netParams, simConfig = simConfig)

    # noise stimulation
    i_noise_list = []
    for cell in sim.net.cells:
        i_noise = h.INoise(cell.secs['soma']['hObj'](0.5))
        i_noise.delay = 0
        i_noise.dur = simConfig.duration
        i_noise.std = 0.3
        # i_noise.seed(cell.gid)
        i_noise_list.append(i_noise)

    sim.runSim()                          # run parallel Neuron simulation
    sim.gatherData()                      # gather spiking data and cell info from each node
    sim.saveData()                        # save params, cell info and sim output to file (pickle,mat,txt,etc)
    sim.analysis.plotData()               # plot spike raster

    if sim.allSimData['spkt'] == []:
        return 0
    else:
        spike_dict = {}
        all_spike_times = sim.allSimData['spkt']
        # print(sim.allSimData['spkid'])
        for i in range(1, 10 + 1):
            spike_times_i = [
                all_spike_times[j]
                for j, spike_id in enumerate(sim.allSimData['spkid'])
                if (100*(i-2) + initial_spike_a <= spike_id <= 100*(i-1) + initial_spike_a and (17.5 * i - 15 <= all_spike_times[j] <= 17.5 * i + 15))
            ]
            if len(spike_times_i) < 2:
                max_cluster = spike_times_i
            else:
                X = np.array(spike_times_i).reshape(-1, 1)
                db = DBSCAN(eps = 5, min_samples=2)
                db.fit(X)

                labels = db.labels_

                # Extract unique clusters
                unique_labels = set(labels)
                unique_labels.discard(-1)  # Remove noise label

                max = 0
                for label in unique_labels:
                    # Extract points belonging to the current cluster
                    cluster_points = X[labels == label].flatten()
                    if len(cluster_points) > max:
                        max_cluster = cluster_points
                        max = len(cluster_points)
            
            # Calculate mean and count
            spike_dict[i] = max_cluster
            print(len(max_cluster))

    stdvar_array = []
    spike_count_array = []    
    for i in range(1, 10 + 1):
        if i in spike_dict:
            spike_times = spike_dict[i]
            stdvar_array.append(np.std(spike_times))
            spike_count_array.append(len(spike_times))
    
    return stdvar_array, spike_count_array


plt.figure(figsize=(8, 8))

#### Fig 3-b ####
# Plot and add arrows for spka
for i in np.arange(0, 3.2, 0.4):
    # Plot and add arrows for spka
    spkvar, spka = run_single_packet_w(90, i, 20, 2)
    a_in = np.concatenate(([i], spkvar[:-1]))
    a_out = spkvar[:]
    plt.plot(a_in, a_out, '-o', markersize=4, color='blue', label=f'spkvar_{i}')
    for i in range(len(a_in) - 1):
        plt.annotate('',
                    xy=(a_in[i+1], a_out[i+1]),
                    xytext=(a_in[i], a_out[i]),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=1),
                    )
        
# for i in np.arange(0, 5, 0.5):
#     # Plot and add arrows for spka
#     spkvar, spka = run_single_packet_w(20, i, 20, 2)
#     a_in = np.concatenate(([i], spkvar[:-1]))
#     a_out = spkvar[:]
#     plt.plot(a_in, a_out, '-o', markersize=4, color='orange', label=f'spkvar_{i}')
#     for i in range(len(a_in) - 1):
#         plt.annotate('',
#                     xy=(a_in[i+1], a_out[i+1]),
#                     xytext=(a_in[i], a_out[i]),
#                     arrowprops=dict(arrowstyle='->', color='orange', lw=1),
#                     )


# Add y=x line
plt.plot([0, 5], [0, 5], 'k--', alpha=0.7)

# Set labels and title
plt.xlabel('$sigma_{in}$ (spikes)', fontsize=12)
plt.ylabel('$sigma_{out}$ (spikes)', fontsize=12)
plt.title('Spike Propagation variance', fontsize=14)

# Set axis limits
plt.xlim(0, 5)
plt.ylim(0, 5)

# Add grid
plt.grid(True, linestyle='--', alpha=0.7)

# Add legend
plt.legend()

# Adjust layout and display
plt.tight_layout()
plt.savefig('fig3_b.png', dpi=300, bbox_inches='tight')