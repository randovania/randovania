import cython
from cpython.ref cimport PyObject, Py_INCREF, Py_DECREF
from cython.cimports.libcpp.utility import pair
from cython.cimports.libcpp.vector import vector
from cython.cimports.libcpp.deque import deque

from cython.cimports.randovania._native_helper import PyRef
from cython.cimports.randovania.graph.graph_requirement import (
    GraphRequirementSetRef
)

cdef extern from *:
    """
    class ProcessNodesState {
    public:
        std::vector<int> checked_nodes;
        std::deque<int> nodes_to_check;
        std::vector<int> game_states_to_check;
        std::vector<std::pair<GraphRequirementSetRef, bool>> satisfied_requirement_on_node;

        ProcessNodesState() {}
    };
    """

    cdef cppclass ProcessNodesState:
        vector[int] checked_nodes
        deque[int] nodes_to_check
        vector[int] game_states_to_check
        vector[pair[GraphRequirementSetRef, bool]] satisfied_requirement_on_node

        ProcessNodesState()

