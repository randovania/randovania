import cython
from cpython.ref cimport PyObject, Py_INCREF, Py_DECREF
from cython.cimports.libcpp.utility import pair

from cython.cimports.randovania.lib.cython_helper import IndexQueue, PyRef, pvector
from cython.cimports.randovania.graph.graph_requirement import (
    GraphRequirementSetRef
)

cdef extern from *:
    """
    #include "randovania/lib/native/pool.hpp"

    class ProcessNodesState {
    public:
        rdv::pvector<int> checked_nodes;
        rdv::IndexQueue<int> nodes_to_check;
        rdv::pvector<int> game_states_to_check;
        rdv::pvector<std::pair<GraphRequirementSetRef, bool>> satisfied_requirement_on_node;

        ProcessNodesState() {}
    };
    """

    cdef cppclass ProcessNodesState:
        pvector[int] checked_nodes
        IndexQueue[int] nodes_to_check
        pvector[int] game_states_to_check
        pvector[pair[GraphRequirementSetRef, bool]] satisfied_requirement_on_node

        ProcessNodesState()

