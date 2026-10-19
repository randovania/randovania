from cython.cimports.libcpp.vector import vector
cimport cython

cdef extern from "randovania/lib/native/bitmask.hpp" namespace "rdv" nogil:
    cdef cppclass BitmaskData:
        BitmaskData() except +
        void set_bit(long long index) except +
        void unset_bit(long long index)
        bint is_set(long long index)
        void union "union_with"(const BitmaskData& other) except +
        bint share_at_least_one_bit(const BitmaskData& other)
        bint is_subset_of(const BitmaskData& other)
        bint is_empty()
        int num_set_bits()
        bint equals_to(const BitmaskData& other)
        unsigned long long hash_value()
        BitmaskData copy() except +
        vector[size_t] get_set_bits() except +

@cython.final
cdef class Bitmask:
    cdef BitmaskData data

    @staticmethod
    cdef Bitmask create_native()

    cpdef bint equals_to(self, Bitmask other)
    cpdef unsigned long long hash_value(self)
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
