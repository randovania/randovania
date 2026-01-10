import cython

# Define a custom hash function for std::pair<int, int>
cdef extern from * nogil:
    """
    #include <utility>
    #include <functional>
    #include <queue>

    namespace std {
        template<>
        struct hash<std::pair<int, int>> {
            size_t operator()(const std::pair<int, int>& p) const noexcept {
                // Combine the hashes of the two integers
                size_t h1 = std::hash<int>{}(p.first);
                size_t h2 = std::hash<int>{}(p.second);
                return h1 ^ (h2 << 1);
            }
        };
    }

    template <typename T>
    using min_priority_queue = std::priority_queue<T, std::vector<T>, std::greater<T>>;

    struct SearchHeapEntry {
        int cost;
        int counter;
        int node;

        SearchHeapEntry() {}
        SearchHeapEntry(int a, int b, int c)
        : cost(a), counter(b), node(c) {}

        bool operator>(const SearchHeapEntry& other) const {
            if (cost != other.cost) return cost > other.cost;
            if (counter != other.counter) return counter > other.counter;
            return node > other.node;
        }
    };
    """

    cdef cppclass min_priority_queue[T]:
        min_priority_queue() except +
        min_priority_queue(min_priority_queue&) except +
        bint empty()
        void pop()
        void push(T&)
        size_t size()
        T& top()

    cdef cppclass SearchHeapEntry:
        int cost
        int counter
        int node

        SearchHeapEntry()
        SearchHeapEntry(int, int, int)
