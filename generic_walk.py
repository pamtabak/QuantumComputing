"""
Script to perform a quantum walk on a graph with structure specified by 
boolean functions (shifts and aditions) over the qbit state representation. It 
offers a generalization of quantum walks performed over cycles, hyper cycles,
grids and some other types of graphs which can be composed by additions of the
qubit state boolean representation, e.g a cycle is formed by using a constant
addition on a vertex state representation (|0000> is adjacent to |0001> and 
|1111> in a 16-vertex cycle).

In order to achieve genaralization, the functions can be visualized following a
coordinate approach. To exemplify, one can define a closed grid graph by 
assigning each vertex a label (x, y), and stating that its neighbors are 
(x + 1, y), (x-1, y), (x,y + 1) and (x, y -1). A simple representation of this
strtucture using qbits can be visualized looking at a state |xyzw> as the state
|(x,y), (z,w)>, where each pair qbits define a coordinate.

To expand even further the power of description, a coordinate can be specified
to be any combination of qbit states. In essence, the quantum walk operates 
by selecting a coordinate to move on. This procedure make it possible to discard
the need of creating the graph in memory, since, on each step, the neighbors of
a vertex can be achieved applying a coordinate function.

This type of Quantum Walk follows a unitary evolution by an operator
U = SC, where S permutes the basis state and C becomes the coin operator.
"""


import sys

import projectq.setups.default

from projectq import MainEngine
from projectq.ops import H, Measure, CNOT, X, Swap
from projectq.meta import Dagger, Control
from projectq.types import WeakQubitRef, Qureg

from numpy import cumsum, log2, base_repr


################################################################################
#---------------Qubit operations-----------------------------------------------
################################################################################

# Performs a controlled gate mixing off controls, active when qubit is 0, and
#  normal controls. active when qubit is 1. Sel is a binary array referencing
#  which qubits will be off and which will be normal.
#
def generic_control(mask, controls, targets, gate, eng, state):

	flipflop_control(mask, controls, state)

	with Control(eng, [state[c] for c in controls]): # allow mutiple target bits
		for t in targets:
			gate | state[t]

	flipflop_control(mask, controls, state)


# Swap bits to be use in off control. The mask array specifies which bit will be
#  flipped. Two consequent calls of this function will maintain the system state
#  related to the involved q-bits if nothing is performed on them.
#
def flipflop_control(mask, controls, state):
	for j in range(len(mask)): # prepare controls evaluated on qubits
		if not mask[j]:
			X | state[controls[j]]



# Performs addition and subtraction on qubit states as if they were binary 
#  strings. Addition / subtraction is selected by inc=1 / inc=0, while the 
#  consntant number added to the state representation defined by the param 
#  const.
#
def cyclic_adder(eng, state, q_target, q_control, const=1, inc=1):

	num_of_targets = len(q_target)
	c_mask = num_of_targets * [inc]

	for j in range(const):
		for i in range(num_of_targets):

			# outer control structure, given by direction
			with Control(eng, [state[c_bit] for c_bit in q_control]):
				generic_control( # increment circuit needs also inner control
					c_mask[i + 1:],
					q_target[i + 1:],
					[q_target[i]], X, eng, state)


# Generic cyclic shift operator. It shifts qbits on a given state to left or
#  right depending on the specified 'right' parameter. The number of shifts is
#  specified by 'const'.
#
def cyclic_shift(
	eng, state, q_target, q_control, const=1, right=1):

	# if right, bits must be swapped with last
	# if left, bits must be swapped with first
	swap_ref = q_target[right * (len(q_target) - 1) + (1-right) * 0]

	# excludes first or last bit from iteration given the direction
	range_params = right * [len(q_target) - 1] + \
				(1 - right) * [1, len(q_target)]

	for s in range(const):
		for i in range(*range_params):
			with Control(eng, [state[c_bit]  for c_bit in q_control]):
				Swap | (state[q_target[i]], state[swap_ref])


# Generic pipeline to apply functions over specified coordinates. The coin 
#  states defines when the given functions will be applied. This behavior is 
#  performed with the flipflop_control function.
#
def apply_on_coord_given_control(
	eng, state, q_target, q_control, c_mask, q_funcs, params):

	flipflop_control(c_mask, q_control, state)

	# apply all the functions referenced by the same coin state
	for k in range(len(q_funcs)):
		print(q_funcs[k], params[k], q_target, "coord function")
		q_funcs[k](eng, state, q_target, q_control, *params[k])

	flipflop_control(c_mask, q_control, state)



################################################################################
#-------------------------Functions related to coin states ---------------------
################################################################################


# Compute how many coin qbits will be needed for the number of degrees of 
#  freedom specified by coords (its length).
#
def num_coin_qbits(coords):
	return int(log2(len(coords))) + 1


# Pads a given boolean state to the number of bits needed.
#
def fill_state(state, n_qbits):
	if len(state) < n_qbits:
		return [0] * 1 + state
	return state

# Maps a integer into its binary representation as an integer list. It will make
#  it uniform, creating each list with 'n_qbits' elements, padding with 0 by the
#  left when needed.
#
def int_to_state(val, n_qbits):
	return fill_state([int(q) for q in base_repr(val)], n_qbits)


# Given a list of coin specifications for each degree of freedom, creates a 
#  the correspondent list of binary states to act as control for walk steps.
#
def define_coin_state(coins):
	coin_qbits = num_coin_qbits(coins)
	return [(
		int_to_state(coin[0], coin_qbits),
		int_to_state(coin[1], coin_qbits)) for coin in coins]

# Create a superposition state for coins. Assumes the number of coin states is a
#  power of 2.
#
def coin_superposition(state, coin_qbits):
	for i in coin_qbits:
		H | state[i]


################################################################################
#------------ Initializers -----------------------------------------------------
################################################################################


# Allocated needed qbits taking into account the coin dimension.
#
def create_register(n_qbits, coords):
	eng = MainEngine()
	n_cqbit = num_coin_qbits(coords)
	return eng, eng.allocate_qureg(n_qbits + n_cqbit), \
		list(range(n_qbits, n_qbits + n_cqbit))


# Parser for inputs defining a graph structure which the random walk will take 
#  place. It's based on the concept of coordinates where each tuple of 
#  'func_tuples' will define a degree of freedom. It demands that both inputs 
#  have the same length. The 'logical_coords' parameter specifies, for each
#  degree of freedom, the group of qbits that will be used to represent it.
#  As an example, the input [('sm1')], [(4)] represents a cyclic graph with 16
#  nodes.
#
def function_compiler(func_tuples, logical_coords):

	func_dict = {"sh": cyclic_shift, "sm": cyclic_adder}

	assert (len(func_tuples) == len(logical_coords)), \
		"One function for each coordinate!"

	coord_funcs = list()
	d_freedom = len(func_tuples)
	params = list()

	for j in range(d_freedom): # iterate over coordinates
		commands = func_tuples[j].replace(" ","").split(",")
		coord_funcs += [[func_dict[command[:2]] for command in commands]]
		params += [[int(command[2:]) for command in commands]]

	return coord_funcs, params


# Main function to walk on a graph defined by functions applied on qbit state 
#  coordinates. The 'coin_rep' param specifies which coin state will be used to
#  move on each coordinate.
#
def walk(n_qbits, steps, funcs, coords, coin_rep):

	coins = define_coin_state(coin_rep)
	coord_funcs, params = function_compiler(funcs, coords)
	eng, state, coin_qbits = create_register(n_qbits, coords)
	coin_superposition(state, coin_qbits)

	for s in range(steps):
		for c in range(len(coins)):

			# move in the direction specified by coords[c]
			apply_on_coord_given_control(
				eng, state, coords[c], coin_qbits, coins[c][0],
				coord_funcs[c], [(i, 1) for i in params[c]])

			# move in the direction specified by coords[c], in the 
			#  opposite orientation
			apply_on_coord_given_control(
				eng, state, coords[c], coin_qbits, coins[c][1],
				list(reversed(coord_funcs[c])), [(i, 0) for i in params[c]])

	# print output
	Measure | (state)
	for node in state:
		print(int(node))


# walk on a grid
test_cycle = [("sm1"), ("sm1")]
coords = [(0, 1), (2, 3)]
coins = [(1, 0), (2, 3)]
steps = 1
walk(4, steps, test_cycle, coords, coins)
