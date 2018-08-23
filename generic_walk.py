import sys

import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X, Swap
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg

from numpy import cumsum, log2


"""
((sm1))
|i_1,...,i_n> = |x>
|x + 1>, |x - 1>
|(i_1,...,i_k)(i_k+1,...i_n)> = |x, y>
|x + 1, y>, |x-1, y>,...


|010> -> |001>,|100>


Moedas para escolher uma estrutura de vizinhança
Moedas para as coordenadas



[
 ((sh2, sm1, sh1, sm5)),
 ((sh2, sm1, sh1, sm5), (sh1, sm2), (sm4, sh1)),
 ((sh3, sm1, sh2, sm5), (sh1, sm2)),
]
[(10), (3,2,5), (2,8)]

"""


# Performs a controlled gate mixing off controls, active when qubit is 0, and
#  normal controls. active when qubit is 1. Sel is a binary array referencing
#  which qubits will be off and which will be normal.
#
def generic_control(sel, controls, targets, gate, eng, nodes):
	prepare_control(sel, controls, eng, nodes)

	with Control(eng, [nodes[c] for c in controls]): # allow mutiple target bits
		for t in targets:
			gate | nodes[t]

	clean_control(mask, controls, eng, nodes)


def prepare_control(mask, controls, eng, nodes):
	for j in range(len(mask)): # prepare controls evaluated on qubits
		if not mask[j]:
			X | nodes[controls[j]]


def clean_control(mask, controls, eng, nodes):
	for j in range(len(mask)): # clean prepared states
		if not mask[j]:
			X | nodes[controls[j]]


# Performs addition and subtraction on qubit states as if they were binary 
#  strings. Addition / subtraction is selected by inc=1 / inc=0, while the 
#  consntant number added to the state representation defined by the param 
#  const.
#
def cyclic_adder(eng, nodes, n_qbits, const=1, inc=1):
	control_bit = n_qbits - 1
	for j in range(const):
		for i in range(control_bit):
			sel = [inc] * (control_bit - i) 
			generic_control(
				sel, list(range(i + 1, n_qbits)), [i], X, eng, nodes)


# Shift right or left the binary string represented in nodes by a constant 
#  displacement.
# coord, quantidade de shift, mascara do controle
#
def cyclic_shift(
	eng, state, q_target, q_control, c_mask, n_qbits, const=1, right=1):

	prepare_control(c_mask, q_control, eng, state)

	if (right):
		for s in range(const):
			for i in range(len(q_target) - 1):
				Swap | (nodes[q_target[i]], nodes[len(q_target) - 1])
	else:
		for s in range(const):
			for i in range(1, len(q_target) - 1):
				Swap | (nodes[q_target[i]], nodes[q_target[0]])

	clean_control(c_mask, q_control, eng, state)



def function_compiler(func_tuples, coord_size):

	func_dict = {"sh": cyclic_shift, "sm": cyclic_adder}

	assert (len(func_tuples) == len(coord_size)), "One function for each coordinate!"
	neighborhoods = list()
	params = list()
	num_of_neighs = len(func_tuples)

	for i in range(num_of_neighs): # iterate over neighbor structures
		for j in range(len(func_tuples[i])): # iterate over coordinates
			commands = func_tuples[i][j].replace(" ","").split(",")
			neighborhoods += [[(func_dict[command[:2]], int(command[2:])) \
					for command in commands]]
		params.append(cumsum(coord_size[i]))
	return neighborhoods, params



def degrees_of_freedom(params):
	return sum([sum(len(param)) for param in params])


def num_coin_qbits(params):
	return int(np.log2(degrees_of_freedom(params))) + 1


def create_register(n_qbits, params):
	eng = MainEngine()
	return eng, eng.allocate_qureg(n_qbits + num_coin_qbits(params))



def walk()


def topology_handler(eng, qbits, n_qbits, funcs, params):
	eng
	coin_qbits = 
	n_qbits = len(nodes)

	for i in xrange(n_qbits - coin_qbits, n_qbits):
		H | nodes[i]






func_1 = [
 (("sh2, sm1, sh1, sm5"), ("sh1, sm2"), ("sm4, sh1")),
 (("sh3, sm1, sh2, sm5"), ("sh1, sm2")),
]

coord_size = [(3,2,5), (2,8)]

neighs, params = function_compiler(func_1, coord_size)
print(neighs)
print(params)



# def cyclic_shift
