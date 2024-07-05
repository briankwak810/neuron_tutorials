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
        
# Fig2-(c)
'''
alpha_list = []
s_out_list = []
s_in = 5

for a_in in range(1, 150, 3):
    spkt_list = []
    for i in range(100):
        spkt = run_single_packet(a_in, s_in)
        if spkt != 0:
            spkt_list.append(spkt)

    s_out = np.std(spkt_list)
    alpha = len(spkt_list)/100

    s_out_list.append(s_out)
    alpha_list.append(alpha)

# Create the range of a_in values
a_in_range = range(1, 150, 3)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(a_in_range, alpha_list, 'b-', linewidth=2)

# Add labels and title
plt.xlabel('Input Spike Count (a_in)', fontsize=12)
plt.ylabel('Alpha (Output/Input Ratio)', fontsize=12)
plt.title('Alpha as a Function of Input Spike Count', fontsize=14)

# Add grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Adjust layout to prevent cutting off labels
plt.tight_layout()

# Save the plot
plt.savefig('alpha_vs_a_in.png', dpi=300, bbox_inches='tight')
'''

#Fig2-(d) troubleshooting (at zero)
# a_in = 40
# s_in = 3

# spkt = run_single_packet(a_in, s_in)
# print(f"spkt: {spkt}")

# Fig2-(d)
'''
alpha_list = []
s_out_list = []
zero_list = []
a_in = 20
s_in = 7

for s_in in range(1, 50):
    s_in /= 10
    spkt_list = []
    for i in range(100):
        spkt = run_single_packet(a_in, s_in)
        if spkt != 0:
            spkt_list.append(spkt)

    if (spkt_list == []):
        zero_list.append(s_in)

    s_out = np.std(spkt_list)
    alpha = len(spkt_list)/100

    s_out_list.append(s_out)
    alpha_list.append(alpha)

print(zero_list)

# Create the range of a_in values
s_in_range = [i/10 for i in range(1, 50)]

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(s_in_range, s_out_list, 'b-', linewidth=2)

# Add labels and title
plt.xlabel('Input variance (s_in)', fontsize=12)
plt.ylabel('Output variance (s_out)', fontsize=12)
plt.title('Output variance as function of input variance', fontsize=14)

# Add grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Adjust layout to prevent cutting off labels
plt.tight_layout()

# Save the plot
plt.savefig('s_out_vs_s_in.png', dpi=300, bbox_inches='tight')
'''

# Fig2-(c) multiple

# Create the range of s_in values
s_in_range = np.arange(0.1, 5.1, 0.1)

# Function to run simulation for a given a_in
def run_simulation(a_in):
    s_out_list = []
    for s_in in s_in_range:
        spkt_list = []
        for i in range(100):
            spkt = run_single_packet(a_in, s_in)
            if spkt != 0:
                spkt_list.append(spkt)
        s_out = np.std(spkt_list) if spkt_list else 0
        s_out_list.append(s_out)
    return s_out_list

# Run simulations for different a_in values
a_in_values = [20, 35, 50]
results = {a_in: run_simulation(a_in) for a_in in a_in_values}

# Create the plot
plt.figure(figsize=(10, 6))

# Plot results for each a_in value
colors = ['b', 'g', 'r']
for a_in, color in zip(a_in_values, colors):
    plt.plot(s_in_range, results[a_in], f'{color}-', linewidth=2, label=f'a_in = {a_in}')

# Add y=x reference line
plt.plot([0, 5], [0, 5], 'k--', alpha=0.7, label='y = x')

# Add labels and title
plt.xlabel('Input variance (s_in)', fontsize=12)
plt.ylabel('Output variance (s_out)', fontsize=12)
plt.title('Output variance as function of input variance', fontsize=14)

# Add grid and legend
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Adjust layout and axis limits
plt.tight_layout()
plt.xlim(0, 5)
plt.ylim(0, 5)

# Save the plot
plt.savefig('s_out_vs_s_in_multiple_a_in.png', dpi=300, bbox_inches='tight')


# #Fig2-(d) multiple
'''
def run_experiment(s_in):
    alpha_list = []
    a_in_range = range(1, 150, 3)
    for a_in in a_in_range:
        spkt_list = []
        for i in range(100):
            spkt = run_single_packet(a_in, s_in)
            if spkt != 0:
                spkt_list.append(spkt)
        alpha = len(spkt_list) / 100
        alpha_list.append(alpha)
    return alpha_list

# Run experiments for different s_in values
s_in_values = [1, 3, 5]
results = {s_in: run_experiment(s_in) for s_in in s_in_values}

# Create the range of a_in values
a_in_range = range(1, 150, 3)

# Create the plot
plt.figure(figsize=(8,8))

# Plot results for each s_in value
colors = ['b', 'g', 'r']
for s_in, color in zip(s_in_values, colors):
    plt.plot(a_in_range, results[s_in], f'{color}-', linewidth=2, label=f'σ = {s_in}')

# Add labels and title
plt.xlabel('Input Spike Count (a_in)', fontsize=12)
plt.ylabel('Alpha (Output/Input Ratio)', fontsize=12)
plt.title('Alpha as a Function of Input Spike Count for Different σ', fontsize=14)

# Add grid and legend
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Adjust layout to prevent cutting off labels
plt.tight_layout()

# Save the plot
plt.savefig('alpha_vs_a_in_multiple_sigma.png', dpi=300, bbox_inches='tight')
'''