import sys

import projectq.setups.default

from projectq 	    import MainEngine
from projectq.ops   import H, Measure, CNOT, X, Swap
from projectq.meta  import Dagger, Control
from projectq.types import WeakQubitRef, Qureg

# works for any complete graph that the graph size is a power of 2.

def walk(eng, nodes, n_qbits, steps, graph_size):
	n_nodes = int(n_qbits/2)
	for n in range(n_nodes, n_qbits):
		H | nodes[n] # coins

	for s in range(steps):
		for i in reversed(range(n_nodes)):
			Swap | (nodes[i], nodes[n_qbits - i - 1])

# standard parameters for script, 10-step walk on a 32-vertex graph
n_qbits    = 10 # we need to double the amount of necessary qubits
graph_size = 32
steps 	   = 10

if len(sys.argv) == 4:
	n_qbits    = int(sys.argv[1]) 
	graph_size = int(sys.argv[2])
	steps      = int(sys.argv[3])

eng   = MainEngine()
nodes = eng.allocate_qureg(n_qbits)
walk(eng, nodes, n_qbits, steps, graph_size)
Measure | (nodes)
for node in nodes:
	print(int(node))