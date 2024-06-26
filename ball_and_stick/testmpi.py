from neuron import h
h.nrnmpi_init()
pc = h.ParallelContext()

print('I am {} of {}'.format(pc.id(), pc.nhost()))
h.quit()