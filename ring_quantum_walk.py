import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg

from numpy import base_repr

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



# Performs a increment(inc = 1) or decrement (inc = 0) counter on states given inc parameter.
def counter(eng, nodes, n_qbits, inc=1):
	control_bit = n_qbits - 1

	for i in range(control_bit):
		sel = [inc] * (control_bit - i) 
		generic_control(sel, list(range(i + 1, n_qbits)), [i], X, eng, nodes)



# Bound counters for cases when graph size (number of vertices) isn't a power 
#  of 2.
def cyclic_increment_bound(eng, nodes, n_qbits, bin_gsize):
	sel = bin_gsize + [1]
	n_of_ones = sum(sel)
	line = 0
	ind = 0
	qubits = list(range(n_qbits))
	params = list()
	while ind < n_of_ones / 2:
		if sel[line]:
			params.append(
				(sel[:line] + sel[line + 1:], qubits[:line] + qubits[line +1 :],
				[line], X, eng, nodes))
			generic_control(*params[-1])
			ind += 1
		line += 1
	for p in params[-2::-1]:
		generic_control(*p)




def cyclic_decrement_bound(eng, nodes, n_qbits, bin_gsize):
	sel = bin_gsize + [0]
	n_of_zeros = n_qbits - sum(sel)
	line = n_qbits - 2
	ind = 0
	qubits = list(range(n_qbits))
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
		bounds[0](eng, nodes, n_qbits, bin_gsize)

		counter(eng, nodes, n_qbits, inc=0) # decrement

		# bound increment iff graph size isn't a power of 2
		bounds[1](eng, nodes, n_qbits, bin_gsize)


eng = MainEngine ()
n_qbits = 6
graph_size = 32
nodes = eng.allocate_qureg(n_qbits)
steps = 10
walk(eng, nodes, n_qbits, steps, graph_size)
Measure | (nodes)
for node in nodes:
	print(int(node))
