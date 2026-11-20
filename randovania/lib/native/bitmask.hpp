// Plain-value bit set backing `Bitmask` and the set/negate masks inside `GraphRequirementList`.
#pragma once

#include <algorithm>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "randovania/lib/native/pool.hpp"

namespace rdv {

class BitmaskData {
public:
    void set_bit(long long index) {
        size_t arr_idx = static_cast<size_t>(index) >> 6;
        uint64_t bit_idx = static_cast<uint64_t>(index) & 63;
        if (arr_idx >= masks_.size()) {
            masks_.resize(arr_idx + 1, 0);
        }
        masks_[arr_idx] |= uint64_t{1} << bit_idx;
    }

    void unset_bit(long long index) {
        size_t arr_idx = static_cast<size_t>(index) >> 6;
        if (arr_idx >= masks_.size()) {
            return;
        }
        uint64_t bit_idx = static_cast<uint64_t>(index) & 63;
        uint64_t mask = uint64_t{1} << bit_idx;
        if (masks_[arr_idx] & mask) {
            masks_[arr_idx] -= mask;
            while (!masks_.empty() && masks_.back() == 0) {
                masks_.pop_back();
            }
        }
    }

    bool is_set(long long index) const {
        size_t arr_idx = static_cast<size_t>(index) >> 6;
        if (arr_idx >= masks_.size()) {
            return false;
        }
        uint64_t bit_idx = static_cast<uint64_t>(index) & 63;
        return (masks_[arr_idx] & (uint64_t{1} << bit_idx)) != 0;
    }

    // Named union_with, not union: `union` is a reserved word in C++.
    void union_with(const BitmaskData& other) {
        if (other.masks_.size() > masks_.size()) {
            masks_.resize(other.masks_.size(), 0);
        }
        for (size_t idx = 0; idx < other.masks_.size(); ++idx) {
            masks_[idx] |= other.masks_[idx];
        }
    }

    bool share_at_least_one_bit(const BitmaskData& other) const {
        size_t last_shared = std::min(masks_.size(), other.masks_.size());
        for (size_t idx = 0; idx < last_shared; ++idx) {
            if (masks_[idx] & other.masks_[idx]) {
                return true;
            }
        }
        return false;
    }

    bool is_subset_of(const BitmaskData& other) const {
        if (masks_.size() > other.masks_.size()) {
            return false;
        }
        for (size_t idx = 0; idx < masks_.size(); ++idx) {
            if ((masks_[idx] & other.masks_[idx]) != masks_[idx]) {
                return false;
            }
        }
        return true;
    }

    bool is_empty() const { return masks_.empty(); }

    int num_set_bits() const {
        int result = 0;
        for (uint64_t mask : masks_) {
            result += std::popcount(mask);
        }
        return result;
    }

    bool equals_to(const BitmaskData& other) const { return masks_ == other.masks_; }

    unsigned long long hash_value() const {
        uint64_t result = 0;
        for (uint64_t mask : masks_) {
            result ^= mask;
        }
        return result;
    }

    BitmaskData copy() const { return *this; }

    // Plain std::vector, relies on Cython's automatic std::vector -> list conversion
    std::vector<size_t> get_set_bits() const {
        std::vector<size_t> result;
        for (size_t idx = 0; idx < masks_.size(); ++idx) {
            uint64_t mask = masks_[idx];
            if (mask == 0) {
                continue;
            }
            long long base_bit_index = static_cast<long long>(idx) * 64;
            int bit_pos = 0;
            uint64_t temp_mask = mask;
            while (temp_mask != 0) {
                if (temp_mask & 1) {
                    result.push_back(static_cast<size_t>(base_bit_index + bit_pos));
                }
                temp_mask >>= 1;
                ++bit_pos;
            }
        }
        return result;
    }

private:
    pvector<uint64_t> masks_;
};

}  // namespace rdv
