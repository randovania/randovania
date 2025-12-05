from cython.cimports.libcpp.unordered_map import unordered_map
from cython.cimports.libcpp.vector import vector
from cython.cimports.randovania.game_description.resources.resource_collection import ResourceCollection
from cython.cimports.randovania.lib.bitmask import Bitmask
from cython.cimports.randovania.lib.cython_helper import PyRef
cimport cython


@cython.final
cdef class GraphRequirementList:
    cdef Bitmask _set_bitmask
    cdef Bitmask _negate_bitmask
    cdef unordered_map[size_t, int] _other_resources
    cdef unordered_map[size_t, int] _damage_resources

    cdef object _resource_db
    cdef bint _frozen

    @staticmethod
    cdef GraphRequirementList from_components(object resource_db, Bitmask set_bitmask, Bitmask negate_bitmask, unordered_map[size_t, int] other_resources, unordered_map[size_t, int] damage_resources)

    @staticmethod
    cdef GraphRequirementList create_empty(object resource_db)

    cdef void _check_can_write(self)
    cdef tuple _complexity_key_for_simplify(self)
    cdef void _simplify_handle_resource(self, size_t resource_index, int amount, bint negate, object progressive_item_info)
    cdef int _single_resource_optimize_logic(self, Bitmask single_req_mask)

    cpdef bint equals_to(self, GraphRequirementList other)
    cpdef bint is_frozen(self)
    cpdef void freeze(self)
    cpdef int num_requirements(self)
    cpdef bint is_trivial(self)
    cpdef set all_resources(self, bint include_damage=?)
    cpdef tuple[int,bint] get_requirement_for(self, object resource, bint include_damage=?)
    cpdef tuple[int,bint] get_requirement_for_index(self, size_t resource_index, bint include_damage=?)
    cpdef bint satisfied(self, ResourceCollection resources, float health)
    cpdef float damage(self, ResourceCollection resources)
    cpdef bint and_with(self, GraphRequirementList merge)
    cpdef GraphRequirementList copy_then_and_with(self, GraphRequirementList right)
    cpdef GraphRequirementList copy_then_remove_entries_for_set_resources(self, ResourceCollection resources)
    cpdef void add_resource(self, object resource, int amount, bint negate)
    cpdef void add_resource_index(self, int resource_index, int amount, bint negate)
    cpdef void add_damage(self, int resource_index, int amount)
    cpdef GraphRequirementList isolate_damage_requirements(self, ResourceCollection resources)
    cpdef bint is_requirement_superset(self, GraphRequirementList subset_req)
    cpdef GraphRequirementList simplify_requirement_list(self, ResourceCollection resources, float health_for_damage_requirements, object node_resources, object progressive_item_info)


cdef extern from *:
    """
    typedef PyRef GraphRequirementListRef;
    """

    ctypedef PyRef GraphRequirementListRef


@cython.final
cdef class GraphRequirementSet:
    cdef vector[GraphRequirementListRef] _alternatives
    cdef bint _frozen

    @staticmethod
    cdef GraphRequirementSet create_empty()

    cdef void _check_can_write(self)

    cpdef bint equals_to(self, GraphRequirementSet other)
    cpdef bint is_frozen(self)
    cpdef void freeze(self)
    cpdef int num_alternatives(self)
    cpdef GraphRequirementList get_alternative(self, int index)
    cpdef void add_alternative(self, GraphRequirementList alternative)
    cpdef void extend_alternatives(self, object alternatives)
    cpdef bint satisfied(self, ResourceCollection resources, float energy)
    cpdef float damage(self, ResourceCollection resources)
    cpdef void all_alternative_and_with(self, GraphRequirementList merge)
    cpdef GraphRequirementSet copy_then_all_alternative_and_with(self, GraphRequirementList merge)
    cpdef GraphRequirementSet copy_then_and_with_set(self, GraphRequirementSet right)
    cpdef GraphRequirementSet copy_then_remove_entries_for_set_resources(self, ResourceCollection resources)
    cpdef void optimize_alternatives(self)
    cpdef bint is_trivial(self)
    cpdef bint is_impossible(self)
    cpdef GraphRequirementSet isolate_damage_requirements(self, ResourceCollection resources)



cdef extern from *:
    """
    typedef PyRef GraphRequirementSetRef;
    """

    ctypedef PyRef GraphRequirementSetRef
