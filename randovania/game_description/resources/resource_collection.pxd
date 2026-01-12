from cython.cimports.libcpp.unordered_map import unordered_map
from cython.cimports.libcpp.vector import vector
from cython.cimports.randovania.lib.bitmask import Bitmask


cdef class ResourceCollection:
    cdef public Bitmask resource_bitmask
    cdef vector[int] _resource_array
    cdef dict[int, object] _existing_resources
    cdef unordered_map[size_t, float] _damage_reduction_cache
    cdef object _resource_database

    cpdef void _resize_array_to_fit(self, size_t size)
    cpdef ResourceCollection duplicate(self)
    cpdef int get(self, object item)
    cpdef int get_index(self, size_t resource_index)
    cpdef bint has_resource(self, object resource)
    cpdef bint is_resource_set(self, object resource)
    cpdef void add_resource(self, object resource, int quantity)
    cpdef void add_resource_gain(self, object resource_gain)
    cpdef float get_damage_reduction(self, size_t resource_index)
