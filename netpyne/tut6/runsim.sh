#!/bin/bash
mpiexec -n $1 nrniv -python -mpi $2  # Run the model