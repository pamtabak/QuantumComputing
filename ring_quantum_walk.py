import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg

eng = MainEngine ()

#node1, node2, node3, node4, subnode
nodes = eng.allocate_qureg(5)

H | nodes[4]

#increment
for i in range(0, 3):
	with Control(eng, nodes[i+1:]):
		X | nodes[i]
X | nodes[3]

#decrement
#since it seems we don`t have an off control: we will implement one
#we will X the control qubits
for i in range(0, 3):
	for j in range(i + 1, 5):
		X | nodes[j]
	with Control(eng, nodes[i+1:]):
		X | nodes[i]
	for j in range(i + 1, 5):
		X | nodes[j]

X | nodes[3]

Measure | (nodes)
for node in nodes:
	print(int(node))