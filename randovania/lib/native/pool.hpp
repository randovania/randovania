// Size-class free-list allocator for the Cython "native" extension modules.
//
// One Pool per compiled module (each .pyd gets its own `pool()` static). Slabs are bump-allocated
// and never freed; freed blocks go back onto a per-size free list. No locking: always used under
// the GIL.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <deque>
#include <memory>
#include <new>
#include <type_traits>
#include <vector>

namespace rdv {

class Pool {
public:
    static constexpr size_t kGranule = 16;
    static constexpr size_t kSmallMax = 1024;
    static constexpr size_t kNumClasses = kSmallMax / kGranule;
    static constexpr size_t kSlabBytes = 64 * 1024;

    struct Stats {
        size_t allocations = 0;
        size_t deallocations = 0;
        size_t freelist_hits = 0;
        size_t slabs_allocated = 0;
        size_t bytes_from_slabs = 0;
        size_t large_allocations = 0;
    };

    Pool() = default;
    Pool(const Pool&) = delete;
    Pool& operator=(const Pool&) = delete;

    void* allocate(size_t bytes) {
        if (bytes == 0) {
            bytes = 1;
        }
        if (bytes > kSmallMax) {
            ++stats_.large_allocations;
            return ::operator new(bytes);
        }

        ++stats_.allocations;
        size_t cls = size_class(bytes);
        Node*& head = free_lists_[cls];
        if (head != nullptr) {
            Node* n = head;
            head = n->next;
            ++stats_.freelist_hits;
            poison(n, class_bytes(cls), 0xA1);
            return n;
        }
        return bump_allocate(class_bytes(cls));
    }

    void deallocate(void* p, size_t bytes) {
        if (p == nullptr) {
            return;
        }
        if (bytes == 0) {
            bytes = 1;
        }
        if (bytes > kSmallMax) {
            ::operator delete(p);
            return;
        }

        ++stats_.deallocations;
        size_t cls = size_class(bytes);
        poison(p, class_bytes(cls), 0xDE);
        Node* n = static_cast<Node*>(p);
        n->next = free_lists_[cls];
        free_lists_[cls] = n;
    }

    const Stats& stats() const { return stats_; }

private:
    struct Node {
        Node* next;
    };

    struct Slab {
        std::unique_ptr<unsigned char[]> data;
        size_t used = 0;
    };

    static size_t size_class(size_t bytes) {
        return (bytes - 1) / kGranule;
    }

    static size_t class_bytes(size_t cls) {
        return (cls + 1) * kGranule;
    }

    static void poison(void* p, size_t bytes, unsigned char value) {
#ifndef NDEBUG
        std::memset(p, value, bytes);
#else
        (void)p;
        (void)bytes;
        (void)value;
#endif
    }

    void* bump_allocate(size_t bytes) {
        if (slabs_.empty() || slabs_.back().used + bytes > kSlabBytes) {
            slabs_.push_back(Slab{std::unique_ptr<unsigned char[]>(new unsigned char[kSlabBytes]), 0});
            ++stats_.slabs_allocated;
        }
        Slab& slab = slabs_.back();
        void* p = slab.data.get() + slab.used;
        slab.used += bytes;
        stats_.bytes_from_slabs += bytes;
        return p;
    }

    Node* free_lists_[kNumClasses] = {};
    // Real std::deque: keeps slab pointers stable as more are pushed. Must not go through the pool.
    std::deque<Slab> slabs_;
    Stats stats_;
};

inline Pool& pool() {
    static Pool instance;
    return instance;
}

template <class T>
struct PoolAllocator {
    using value_type = T;
    using is_always_equal = std::true_type;
    using propagate_on_container_move_assignment = std::true_type;

    PoolAllocator() noexcept = default;
    template <class U>
    PoolAllocator(const PoolAllocator<U>&) noexcept {}

    T* allocate(size_t n) {
        return static_cast<T*>(pool().allocate(n * sizeof(T)));
    }
    void deallocate(T* p, size_t n) noexcept {
        pool().deallocate(p, n * sizeof(T));
    }

    template <class U>
    bool operator==(const PoolAllocator<U>&) const noexcept {
        return true;
    }
    template <class U>
    bool operator!=(const PoolAllocator<U>&) const noexcept {
        return false;
    }
};

template <class T>
using pvector = std::vector<T, PoolAllocator<T>>;

// FIFO queue over a single pool-allocated vector plus a head index; replaces std::deque, which
// on MSVC allocates a new block roughly every 4 pushes.
template <class T>
class IndexQueue {
public:
    void push_back(const T& value) { items_.push_back(value); }

    void pop_front() {
        ++head_;
        compact_if_worthwhile();
    }

    T& front() { return items_[head_]; }
    const T& front() const { return items_[head_]; }

    T& operator[](size_t index) { return items_[head_ + index]; }
    const T& operator[](size_t index) const { return items_[head_ + index]; }

    bool empty() const { return head_ >= items_.size(); }
    size_t size() const { return items_.size() - head_; }

    void clear() {
        items_.clear();
        head_ = 0;
    }

private:
    static constexpr size_t kMinCompactSize = 64;

    void compact_if_worthwhile() {
        if (head_ >= kMinCompactSize && head_ * 2 >= items_.size()) {
            items_.erase(items_.begin(), items_.begin() + static_cast<std::ptrdiff_t>(head_));
            head_ = 0;
        }
    }

    pvector<T> items_;
    size_t head_ = 0;
};

}  // namespace rdv
