import cython
from cpython.ref cimport PyObject, Py_INCREF, Py_DECREF
from cython.cimports.libcpp.utility import pair

from cython.cimports.randovania.lib.cython_helper import IndexQueue, PyRef, pvector
from cython.cimports.randovania.graph.graph_requirement import (
    GraphRequirementSetRef
)

# Per-Logic scratch state for resolver_reach_process_nodes, reused across calls instead of
# rebuilt every time; see ResolverScratch.begin()/reset() in resolver_native.py.
cdef class ResolverScratch:
    cdef pvector[int] checked_nodes
    cdef IndexQueue[int] nodes_to_check
    cdef pvector[int] game_states_to_check
    cdef pvector[pair[GraphRequirementSetRef, bool]] satisfied_requirement_on_node
    cdef pvector[size_t] found_node_order
    cdef public bint in_use
    cdef size_t capacity

    cdef void begin(self, size_t num_nodes) except *
    cdef void reset(self) except *

