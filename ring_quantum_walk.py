import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg


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



# Perform a given number of steps of a cycle
def walk(eng, nodes, n_qbits, steps):
	H | nodes[n_qbits - 1] # uses last bit as coin
	for s in range(steps):
		counter(eng, nodes, n_qbits, inc=1)
		counter(eng, nodes, n_qbits, inc=0)


eng = MainEngine ()
n_qbits = 6
nodes = eng.allocate_qureg(n_qbits)
steps = 1
walk(eng, nodes, n_qbits, steps)
Measure | (nodes)
for node in nodes:
	print(int(node))