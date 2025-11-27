import cython
from cpython.ref cimport PyObject, Py_INCREF, Py_DECREF
from cython.cimports.libcpp.utility import pair
from cython.cimports.libcpp.vector import vector

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
        PyRef() {obj = NULL;}
        PyRef(PyObject* set_obj) {
            Py_XINCREF(set_obj); 
            obj = set_obj;}
        
        ~PyRef() {
            Py_XDECREF(obj);obj = NULL;
        }

        PyRef(const PyRef& other)  {
            Py_XINCREF(other.obj); 
            obj = other.obj;
        }
        PyRef(PyRef&& other) {obj = other.obj; other.obj = NULL;}

        PyRef& operator=(const PyRef& other) {
            Py_XDECREF(obj); 
            Py_XINCREF(other.obj); 
            obj = other.obj;
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
            Py_XDECREF(obj); 
            Py_XINCREF(set_obj); 
            obj = set_obj;
        }

        int has_value() const {return obj != NULL;}
    };
    typedef PyRef DamageStateRef;
    typedef PyRef GraphRequirementSetRef;
    typedef PyRef ResourceInfoRef;
    using GameStateForNodes = std::pair<std::vector<void*>*, std::vector<DamageStateRef>*>;

    struct ProcessNodesState {
        std::vector<PyObject*> checked_nodes;
        std::deque<int> nodes_to_check;
        std::vector<DamageStateRef> game_states_to_check;
        std::vector<std::pair<GraphRequirementSetRef, bool>> satisfied_requirement_on_node;
    };

    """
    cdef cppclass PyRef:
        PyRef()
        PyRef(PyObject* set_obj)
        PyRef(object set_obj)
        object get()
        void release()
        void set(object set_obj)
        int has_value()

    ctypedef PyRef DamageStateRef
    ctypedef PyRef GraphRequirementSetRef
    ctypedef PyRef ResourceInfoRef
   
    cdef cppclass ProcessNodesState:
        vector[PyObject*] checked_nodes
        deque[int] nodes_to_check
        vector[DamageStateRef] game_states_to_check
        vector[pair[GraphRequirementSetRef, bool]] satisfied_requirement_on_node

    ctypedef vector[void*]* VoidPtrVectorPtr
    ctypedef vector[DamageStateRef]* DamageStateRefVectorPtr
    ctypedef pair[VoidPtrVectorPtr, DamageStateRefVectorPtr] GameStateForNodes

