import sys

import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg

from numpy import base_repr

"""
This script implements quantum walks on generic cycles following the circuit
structure defined in 'https://arxiv.org/pdf/0706.0304.pdf' ([1]). It works as a
coinned quantum walk using a single coin qbit and increments and decrements of
the vertex state basis. The coin is represented by a Hadamard gate applied over
a prepared qubit on state |0>.
"""

# Performs a controlled gate mixing off controls, active when qubit is 0, and
#  normal controls. active when qubit is 1. Sel is a binary array referencing
#  which qubits will be off and which will be normal.


def generic_control(sel, controls, targets, gate, eng, nodes):
	for j in range(len(sel)): # prepare controls evaluated on qubits
		if not sel[j]:
			X | nodes[controls[j]]

	with Control(eng, [nodes[c] for c in controls]): # allow mutiple target bits
		for t in targets:
			X | nodes[t]

	for j in range(len(sel)): # clean prepared states
		if not sel[j]:
			X | nodes[controls[j]]


# Performs a increment(inc = 1) or decrement (inc = 0) counter on states given 
#  inc parameter.
def counter(eng, nodes, n_qbits, inc=1):
	control_bit = n_qbits - 1

	for i in range(control_bit):
		sel = [inc] * (control_bit - i) 
		generic_control(sel, list(range(i + 1, n_qbits)), [i], X, eng, nodes)


# Bound counters for cases when graph size (number of vertices) isn't a power 
#  of 2. When incrementing, the state |bin_gsize> must be mapped to the state 
#  |0>.
def cyclic_increment_bound(eng, nodes, n_qbits, bin_gsize):
	sel = bin_gsize + [1]
	n_of_ones = sum(sel)

	line = 0 # index for qubits representing vertex label
	ind = 0 # counter of qbits on state 1

	# auxialiary list to define index of selection qbits for each iteration
	qubits = list(range(n_qbits))

	# list to accumulate parameters used by generic_control to map |bin_gsize>
	#  to |0>
	params = list()
	while ind < n_of_ones:
		if sel[line]:
			params.append(
				(sel[:line] + sel[line + 1:], qubits[:line] + qubits[line +1 :],
				[line], X, eng, nodes))
			generic_control(*params[-1])
			ind += 1
		line += 1

	# When incrementing, it's necessary to fix flipped bits of states that 
	#  activate selectors of previous sections.
	for p in params[-2::-1]:
		generic_control(*p)


# Bound counters for cases when graph size (number of vertices) isn't a power 
#  of 2. When decrementing a vertex label, it's necessary to map the 0 state to
#  the state expressed by bin_gsize.
def cyclic_decrement_bound(eng, nodes, n_qbits, bin_gsize):
	sel = bin_gsize + [0]
	n_of_zeros = n_qbits - sum(sel)

	line = n_qbits - 2 # index for qubits representing vertex label
	ind = 0 # counter of qbits on state 0

	# auxialiary list to define index of selection qbits for each iteration
	qubits = list(range(n_qbits))

	# auxiliary list to gradually define control types for node qubits when
	#  mapping state |0> to |bin_gsize>
	mask = [1] * (n_qbits - 1)
	mask.append(0)

	while ind < n_of_zeros:
		if not sel[line]:
			generic_control(
				mask[:line] + mask[line + 1:],
				qubits[:line] + qubits[line +1 :],
				[line], X, eng, nodes)
			mask[line] = 0
			ind += 1
		line -= 1


# Perform a given number of steps of a cycle
def walk(eng, nodes, n_qbits, steps, graph_size):

	bounds = (lambda eng, nodes, n_qbits, bin_gsize: 0,
			  lambda eng, nodes, n_qbits, bin_gsize: 0)
	bin_gsize = [int(i) for i in base_repr(graph_size - 1)]

	if sum(bin_gsize) != (n_qbits - 1): # allow bounds iff not power of 2
		bounds = (cyclic_increment_bound, cyclic_decrement_bound)

	H | nodes[n_qbits - 1] # uses last bit as coin for cycle

	for s in range(steps):

		counter(eng, nodes, n_qbits, inc=1) # increment

		# bound increment iff graph size isn't a power of 2
		#  see Figure 3 of [1] for more clarification
		bounds[0](eng, nodes, n_qbits, bin_gsize)

		counter(eng, nodes, n_qbits, inc=0) # decrement

		# bound decrement iff graph size isn't a power of 2
		#  see Figure 3 of [1] for more clarification
		bounds[1](eng, nodes, n_qbits, bin_gsize)


# standard parameters for script, 10-step walk on a 32-vertex graph
n_qbits = 6
graph_size = 32
steps = 10

if len(sys.argv) == 4:
	n_qbits = int(sys.argv[1]) 
	graph_size = int(sys.argv[2])
	steps = int(sys.argv[3])

if (2 ** (n_qbits - 1) < graph_size):
	print("Not enough qbits to represent given number of vertices!")
else:	
	eng = MainEngine()
	nodes = eng.allocate_qureg(n_qbits)
	walk(eng, nodes, n_qbits, steps, graph_size)
	Measure | (nodes)
	for node in nodes:
		print(int(node))
