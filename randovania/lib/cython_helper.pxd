import cython
from cpython.ref cimport PyObject, Py_INCREF, Py_DECREF
from cython.cimports.libcpp.vector import vector

cdef extern from "randovania/lib/native/pool.hpp" namespace "rdv" nogil:
    cdef cppclass PoolAllocator[T]:
        pass

    # std::vector, pool-allocated instead of OS heap.
    cdef cppclass pvector[T](vector[T]):
        pvector() except +

    # Pool-backed FIFO, replaces std::deque.
    cdef cppclass IndexQueue[T]:
        IndexQueue() except +
        void push_back(const T&) except +
        void pop_front()
        T& front()
        T& operator[](size_t)
        bint empty()
        size_t size()
        void clear()

    # Diagnostics for the module-local Pool instance.
    cdef cppclass PoolStats "rdv::Pool::Stats":
        size_t allocations
        size_t deallocations
        size_t freelist_hits
        size_t slabs_allocated
        size_t bytes_from_slabs
        size_t large_allocations

    cdef cppclass Pool:
        const PoolStats& stats()

    Pool& pool()

cdef extern from *:
    """
    class PyRef {
        PyObject* obj;
    public:
        
        PyObject* get() {
            if (obj == NULL) {
                Py_INCREF(Py_None);
                return Py_None;
            }
            Py_INCREF(obj);
            return obj;
        }
        PyObject* raw() {
            return obj;
        }
        PyRef() {obj = NULL;}
        PyRef(PyObject* set_obj) {
            Py_XINCREF(set_obj); 
            obj = set_obj;}
        
        ~PyRef() {
            Py_XDECREF(obj);
            obj = NULL;
        }

        PyRef(const PyRef& other)  {
            Py_XINCREF(other.obj); 
            obj = other.obj;
        }
        PyRef(PyRef&& other) {obj = other.obj; other.obj = NULL;}

        PyRef& operator=(const PyRef& other) {
            if (other.obj != obj) {
                Py_XINCREF(other.obj);
                Py_XDECREF(obj);
                obj = other.obj;
            }
            return *this;
        }
        PyRef& operator=(PyRef&& other) {
            Py_XDECREF(obj); 
            obj = other.obj; 
            other.obj = NULL;
            return *this;
        }

        void release() { 
            Py_XDECREF(obj); 
            obj = NULL;
        }

        void set(PyObject* set_obj) {
            if (set_obj != obj) {
                Py_XINCREF(set_obj);
                Py_XDECREF(obj);
                obj = set_obj;
            }
        }

        int has_value() const {return obj != NULL;}
    };

    """
    cdef cppclass PyRef:
        PyRef()
        PyRef(PyObject* set_obj)
        PyRef(object set_obj)
        object get()
        PyObject* raw()
        void release()
        void set(object set_obj)
        int has_value()

