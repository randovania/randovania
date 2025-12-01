from cython.cimports.randovania.lib.bitmask import Bitmask
cimport cython

@cython.final
cdef class WorldGraphNodeConnection:
    cdef public int target
    """The destination node for this connection."""

    cdef public object requirement
    """The requirements for crossing this connection, with all extras already processed."""

    cdef public object requirement_with_self_dangerous
    """`requirement` combined with any resources provided by the source node that are dangerous."""

    cdef public object requirement_without_leaving


cdef class BaseWorldGraphNode:
    cdef public int node_index
    cdef public bint heal
    cdef public list[WorldGraphNodeConnection] connections
    cdef public Bitmask resource_gain_bitmask
    cdef public bint require_collected_to_leave
