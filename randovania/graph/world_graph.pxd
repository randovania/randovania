from cython.cimports.randovania.lib.bitmask import Bitmask
from cython.cimports.randovania.graph.graph_requirement import GraphRequirementSet
from cython.cimports.randovania.game_description.resources.resource_collection import ResourceCollection
cimport cython

@cython.final
cdef class WorldGraphNodeConnection:
    cdef public int target
    """The destination node for this connection."""

    cdef public GraphRequirementSet requirement
    """The requirements for crossing this connection, with all extras already processed."""

    cdef public GraphRequirementSet requirement_with_self_dangerous
    """`requirement` combined with any resources provided by the source node that are dangerous."""

    cdef public GraphRequirementSet requirement_without_leaving


cdef class BaseWorldGraphNode:
    cdef public int node_index
    cdef public bint heal
    cdef public list[WorldGraphNodeConnection] connections
    cdef public Bitmask resource_gain_bitmask
    cdef public Bitmask dangerous_resources
    cdef public bint require_collected_to_leave

    cpdef bint has_all_resources(self, ResourceCollection resources)
