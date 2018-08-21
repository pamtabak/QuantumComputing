import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg


def increment(eng, nodes, n_qbits):
	control_bit = n_qbits - 1
	last_node_bit = n_qbits - 2

	for i in range(0, last_node_bit):
		with Control(eng, nodes[i+1:]):
			X | nodes[i]

	with Control(eng, nodes[control_bit]):
		X | nodes[last_node_bit]


# decrement
# since it seems we don`t have an off control: we will implement one
# we will X the control qubits
def decrement(eng, nodes, n_qbits):
	control_bit = n_qbits - 1
	last_node_bit = n_qbits - 2

	for i in range(0, last_node_bit):
		for j in range(i + 1, n_qbits):
			X | nodes[j]
		with Control(eng, nodes[i+1:]):
			X | nodes[i]
		for j in range(i + 1, n_qbits):
			X | nodes[j]

	X | nodes[control_bit]
	with Control(eng, nodes[control_bit]):
		X | nodes[last_node_bit]
	X | nodes[control_bit]


# Perform a given number of steps of a cycle
def walk(eng, nodes, n_qbits, steps):
	H | nodes[n_qbits - 1] # uses last bit as coin
	for s in range(steps):
		increment(eng, nodes, n_qbits)
		decrement(eng, nodes, n_qbits)


eng = MainEngine ()
n_qbits = 6
nodes = eng.allocate_qureg(n_qbits)
steps = 1
walk(eng, nodes, n_qbits, steps)
Measure | (nodes)
for node in nodes:
	print(int(node))