from cython.cimports.libcpp.vector import vector

cdef class Bitmask:
    cdef public vector[ulonglong] _masks

    @staticmethod
    cdef Bitmask create_native()

    cpdef bint equals_to(self, Bitmask other)
    cpdef void set_bit(self, long long index)
    cpdef void unset_bit(self, long long index)
    cpdef bint is_set(self, long long index)
    cpdef void union(self, Bitmask other)
    cpdef bint share_at_least_one_bit(self, Bitmask other)
    cpdef bint is_subset_of(self, Bitmask other)
    cpdef vector[size_t] get_set_bits(self)
    cpdef int num_set_bits(self)
    cpdef bint is_empty(self)
    cpdef Bitmask copy(self)
