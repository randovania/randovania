from randovania.lib.bitmask import Bitmask


def test_create_empty():
    """Test creating an empty bitmask."""
    bm = Bitmask.create()
    assert bm.is_empty()
    assert bm.num_set_bits() == 0
    assert bm.get_set_bits() == []


def test_set_single_bit():
    """Test setting a single bit."""
    bm = Bitmask.create()
    bm.set_bit(5)
    assert not bm.is_empty()
    assert bm.num_set_bits() == 1
    assert bm.is_set(5)
    assert bm.get_set_bits() == [5]


def test_set_multiple_bits_same_element():
    """Test setting multiple bits within the same 64-bit element."""
    bm = Bitmask.create()
    bm.set_bit(0)
    bm.set_bit(10)
    bm.set_bit(63)
    assert bm.num_set_bits() == 3
    assert bm.is_set(0)
    assert bm.is_set(10)
    assert bm.is_set(63)
    assert not bm.is_set(5)
    assert bm.get_set_bits() == [0, 10, 63]


def test_set_bits_across_elements():
    """Test setting bits that span multiple vector elements."""
    bm = Bitmask.create()
    bm.set_bit(0)  # First element
    bm.set_bit(64)  # Second element
    bm.set_bit(128)  # Third element
    bm.set_bit(192)  # Fourth element
    assert bm.num_set_bits() == 4
    assert bm.is_set(0)
    assert bm.is_set(64)
    assert bm.is_set(128)
    assert bm.is_set(192)
    assert not bm.is_set(63)
    assert not bm.is_set(65)
    assert not bm.is_set(127)
    assert bm.get_set_bits() == [0, 64, 128, 192]


def test_set_same_bit_twice():
    """Test that setting the same bit twice doesn't increase count."""
    bm = Bitmask.create()
    bm.set_bit(42)
    bm.set_bit(42)
    assert bm.num_set_bits() == 1
    assert bm.get_set_bits() == [42]


def test_unset_bit():
    """Test unsetting a bit."""
    bm = Bitmask.create()
    bm.set_bit(10)
    bm.set_bit(20)
    assert bm.is_set(10)
    assert bm.is_set(20)
    bm.unset_bit(10)
    assert bm.num_set_bits() == 1
    assert not bm.is_set(10)
    assert bm.is_set(20)
    assert bm.get_set_bits() == [20]


def test_unset_bit_shrinks_vector():
    """Test that unsetting the last bits shrinks the internal vector."""
    bm = Bitmask.create()
    bm.set_bit(0)
    bm.set_bit(64)
    bm.set_bit(128)

    # Unset from highest to lowest
    bm.unset_bit(128)
    bm.unset_bit(64)
    bm.unset_bit(0)

    assert bm.is_empty()
    assert bm.num_set_bits() == 0
    assert bm.get_set_bits() == []


def test_unset_nonexistent_bit():
    """Test unsetting a bit that was never set."""
    bm = Bitmask.create()
    bm.set_bit(10)
    bm.unset_bit(20)  # Wasn't set
    assert bm.num_set_bits() == 1
    assert bm.get_set_bits() == [10]


def test_equals_to_same():
    """Test equality between identical bitmasks."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.set_bit(100)

    bm2.set_bit(5)
    bm2.set_bit(100)

    assert bm1.equals_to(bm2)
    assert bm1 == bm2


def test_equals_to_different():
    """Test inequality between different bitmasks."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm2.set_bit(10)

    assert not bm1.equals_to(bm2)
    assert bm1 != bm2
    assert bm1.get_set_bits() == [5]
    assert bm2.get_set_bits() == [10]


def test_equals_to_different_sizes():
    """Test inequality when bitmasks have different vector sizes."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(10)
    bm2.set_bit(10)
    bm2.set_bit(200)  # Forces larger vector

    assert not bm1.equals_to(bm2)
    assert bm1.get_set_bits() == [10]
    assert bm2.get_set_bits() == [10, 200]


def test_copy_simple():
    """Test copying a simple bitmask."""
    bm1 = Bitmask.create()
    bm1.set_bit(5)
    bm1.set_bit(10)

    bm2 = bm1.copy()

    assert bm1.equals_to(bm2)
    assert bm1 == bm2
    assert bm1.get_set_bits() == [5, 10]
    assert bm2.get_set_bits() == [5, 10]


def test_copy_independence():
    """Test that copied bitmasks are independent."""
    bm1 = Bitmask.create()
    bm1.set_bit(5)

    bm2 = bm1.copy()
    bm2.set_bit(10)

    assert bm1.num_set_bits() == 1
    assert bm2.num_set_bits() == 2
    assert not bm1.equals_to(bm2)
    assert bm1.get_set_bits() == [5]
    assert bm2.get_set_bits() == [5, 10]


def test_copy_multiple_elements():
    """Test copying a bitmask with multiple vector elements."""
    bm1 = Bitmask.create()
    bm1.set_bit(0)
    bm1.set_bit(64)
    bm1.set_bit(128)
    bm1.set_bit(192)

    bm2 = bm1.copy()

    assert bm1.equals_to(bm2)

    # Modify copy and verify independence
    bm2.set_bit(256)
    assert not bm1.equals_to(bm2)
    assert bm1.num_set_bits() == 4
    assert bm2.num_set_bits() == 5
    assert bm1.get_set_bits() == [0, 64, 128, 192]
    assert bm2.get_set_bits() == [0, 64, 128, 192, 256]


def test_union_empty_with_empty():
    """Test union of two empty bitmasks."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.union(bm2)

    assert bm1.is_empty()
    assert bm1.get_set_bits() == []


def test_union_with_empty():
    """Test union with an empty bitmask."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.union(bm2)

    assert bm1.num_set_bits() == 1
    assert bm1.get_set_bits() == [5]


def test_union_non_overlapping_same_element():
    """Test union of non-overlapping bits in the same element."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm2.set_bit(10)

    bm1.union(bm2)

    assert bm1.num_set_bits() == 2
    assert bm1.get_set_bits() == [5, 10]


def test_union_overlapping():
    """Test union with overlapping bits."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.set_bit(10)
    bm2.set_bit(10)
    bm2.set_bit(15)

    bm1.union(bm2)

    assert bm1.num_set_bits() == 3
    assert bm1.get_set_bits() == [5, 10, 15]


def test_union_extends_to_larger_size():
    """Test that union properly extends when other has more elements."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(10)  # Only first element
    bm2.set_bit(10)
    bm2.set_bit(128)  # Third element

    bm1.union(bm2)

    assert bm1.num_set_bits() == 2
    assert bm1.get_set_bits() == [10, 128]


def test_union_multiple_elements():
    """Test union with multiple vector elements."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(0)
    bm1.set_bit(64)

    bm2.set_bit(64)
    bm2.set_bit(128)

    bm1.union(bm2)

    assert bm1.num_set_bits() == 3
    assert bm1.get_set_bits() == [0, 64, 128]


def test_union_preserves_original_bits():
    """Test that union preserves bits from both bitmasks."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.set_bit(200)

    bm2.set_bit(100)
    bm2.set_bit(300)

    bm1.union(bm2)

    assert bm1.num_set_bits() == 4
    assert bm1.get_set_bits() == [5, 100, 200, 300]
    assert bm1.get_set_bits() == [5, 100, 200, 300]


def test_union_does_not_modify_other():
    """Test that union doesn't modify the other bitmask."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm2.set_bit(10)

    original_count = bm2.num_set_bits()
    bm1.union(bm2)

    assert bm2.num_set_bits() == original_count
    assert bm2.get_set_bits() == [10]
    assert bm2.get_set_bits() == [10]


def test_is_subset_of_empty():
    """Test subset relationship with empty bitmasks."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    assert bm1.is_subset_of(bm2)
    assert bm1.get_set_bits() == []
    assert bm2.get_set_bits() == []


def test_is_subset_of_():
    """Test that a bitmask is a subset of it."""
    bm = Bitmask.create()
    bm.set_bit(5)
    bm.set_bit(10)

    assert bm.is_subset_of(bm)
    assert bm.get_set_bits() == [5, 10]
    assert bm.get_set_bits() == [5, 10]


def test_is_subset_of_true():
    """Test proper subset relationship."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)

    bm2.set_bit(5)
    bm2.set_bit(10)

    assert bm1.is_subset_of(bm2)
    assert bm1.get_set_bits() == [5]
    assert bm2.get_set_bits() == [5, 10]


def test_is_subset_of_false():
    """Test when not a subset."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.set_bit(15)

    bm2.set_bit(5)
    bm2.set_bit(10)

    assert not bm1.is_subset_of(bm2)


def test_is_subset_of_larger_size_false():
    """Test subset returns false when  has more elements."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(200)
    bm2.set_bit(10)

    assert not bm1.is_subset_of(bm2)


def test_is_subset_of_multiple_elements():
    """Test subset with multiple vector elements."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(10)
    bm1.set_bit(100)

    bm2.set_bit(10)
    bm2.set_bit(100)
    bm2.set_bit(200)

    assert bm1.is_subset_of(bm2)
    assert bm1.get_set_bits() == [10, 100]
    assert bm2.get_set_bits() == [10, 100, 200]


def test_share_at_least_one_bit_false():
    """Test no shared bits."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm2.set_bit(10)

    assert not bm1.share_at_least_one_bit(bm2)
    assert bm1.get_set_bits() == [5]
    assert bm2.get_set_bits() == [10]


def test_share_at_least_one_bit_true():
    """Test with shared bits."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.set_bit(10)

    bm2.set_bit(10)
    bm2.set_bit(15)

    assert bm1.share_at_least_one_bit(bm2)
    assert bm1.get_set_bits() == [5, 10]
    assert bm2.get_set_bits() == [10, 15]


def test_share_at_least_one_bit_multiple_elements():
    """Test sharing bits across multiple elements."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(10)
    bm1.set_bit(200)

    bm2.set_bit(100)
    bm2.set_bit(200)

    assert bm1.share_at_least_one_bit(bm2)
    assert bm1.get_set_bits() == [10, 200]
    assert bm2.get_set_bits() == [100, 200]


def test_share_at_least_one_bit_different_sizes():
    """Test sharing with different vector sizes."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(10)
    bm2.set_bit(200)

    assert not bm1.share_at_least_one_bit(bm2)
    assert bm1.get_set_bits() == [10]
    assert bm2.get_set_bits() == [200]


def test_hash_consistency():
    """Test that equal bitmasks have the same hash."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm1.set_bit(100)

    bm2.set_bit(5)
    bm2.set_bit(100)

    assert hash(bm1) == hash(bm2)
    assert bm1.get_set_bits() == [5, 100]
    assert bm2.get_set_bits() == [5, 100]


def test_hash_different():
    """Test that different bitmasks typically have different hashes."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(5)
    bm2.set_bit(10)

    # Note: hashes can collide, but should be different most of the time
    # This is not a strict requirement, just a practical check
    assert hash(bm1) != hash(bm2)
    assert bm1.get_set_bits() == [5]
    assert bm2.get_set_bits() == [10]


def test_num_set_bits_large():
    """Test counting bits across many elements."""
    bm = Bitmask.create()

    # Set bits across multiple elements
    for i in range(0, 500, 7):  # Every 7th bit up to 500
        bm.set_bit(i)

    expected_count = len(range(0, 500, 7))
    assert bm.num_set_bits() == expected_count
    assert bm.get_set_bits() == list(range(0, 500, 7))


def test_complex_operations_sequence():
    """Test a complex sequence of operations."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    # Build first bitmask
    for i in [0, 5, 64, 128, 200]:
        bm1.set_bit(i)

    # Build second bitmask
    for i in [5, 10, 64, 150, 300]:
        bm2.set_bit(i)

    # Create a copy before union
    bm1_copy = bm1.copy()

    # Perform union
    bm1.union(bm2)

    # Verify results
    assert bm1.num_set_bits() == 8  # 0, 5, 10, 64, 128, 150, 200, 300
    assert bm1_copy.num_set_bits() == 5  # Copy unchanged
    assert bm1.is_subset_of(bm1)
    assert bm1_copy.is_subset_of(bm1)
    assert bm2.is_subset_of(bm1)
    assert bm1.share_at_least_one_bit(bm2)
    assert bm1.share_at_least_one_bit(bm1_copy)
    assert bm1.get_set_bits() == [0, 5, 10, 64, 128, 150, 200, 300]
    assert bm1_copy.get_set_bits() == [0, 5, 64, 128, 200]
    assert bm2.get_set_bits() == [5, 10, 64, 150, 300]


def test_edge_case_bit_63():
    """Test boundary at bit 63 (last bit of first element)."""
    bm = Bitmask.create()
    assert not bm.is_set(63)
    bm.set_bit(63)
    assert bm.num_set_bits() == 1
    assert bm.is_set(63)
    bm.unset_bit(63)
    assert bm.is_empty()
    assert not bm.is_set(63)
    assert bm.get_set_bits() == []


def test_edge_case_bit_64():
    """Test boundary at bit 64 (first bit of second element)."""
    bm = Bitmask.create()
    assert not bm.is_set(64)
    bm.set_bit(64)
    assert bm.num_set_bits() == 1
    assert bm.is_set(64)
    bm.unset_bit(64)
    assert bm.is_empty()
    assert not bm.is_set(64)
    assert bm.get_set_bits() == []


def test_large_bit_index():
    """Test setting a very large bit index."""
    bm = Bitmask.create()
    assert not bm.is_set(10000)
    bm.set_bit(10000)
    assert bm.num_set_bits() == 1
    assert not bm.is_empty()
    assert bm.is_set(10000)
    assert not bm.is_set(9999)
    assert not bm.is_set(10001)
    assert bm.get_set_bits() == [10000]


def test_is_set_empty_bitmask():
    """Test is_set on an empty bitmask."""
    bm = Bitmask.create()
    assert not bm.is_set(0)
    assert not bm.is_set(10)
    assert not bm.is_set(64)
    assert not bm.is_set(1000)
    assert bm.get_set_bits() == []


def test_is_set_after_operations():
    """Test is_set after various operations."""
    bm = Bitmask.create()

    # Set some bits
    bm.set_bit(5)
    bm.set_bit(70)
    bm.set_bit(150)

    assert bm.is_set(5)
    assert bm.is_set(70)
    assert bm.is_set(150)
    assert not bm.is_set(4)
    assert not bm.is_set(71)

    # Unset a bit
    bm.unset_bit(70)
    assert not bm.is_set(70)
    assert bm.is_set(5)
    assert bm.is_set(150)
    assert bm.get_set_bits() == [5, 150]


def test_is_set_across_union():
    """Test is_set after union operations."""
    bm1 = Bitmask.create()
    bm2 = Bitmask.create()

    bm1.set_bit(10)
    bm1.set_bit(100)

    bm2.set_bit(50)
    bm2.set_bit(200)

    bm1.union(bm2)

    assert bm1.is_set(10)
    assert bm1.is_set(50)
    assert bm1.is_set(100)
    assert bm1.is_set(200)
    assert not bm1.is_set(11)
    assert not bm1.is_set(51)
    assert bm1.get_set_bits() == [10, 50, 100, 200]


def test_is_set_after_copy():
    """Test is_set on copied bitmasks."""
    bm1 = Bitmask.create()
    bm1.set_bit(42)
    bm1.set_bit(100)

    bm2 = bm1.copy()

    assert bm2.is_set(42)
    assert bm2.is_set(100)
    assert not bm2.is_set(43)

    # Modify copy
    bm2.set_bit(200)
    assert bm2.is_set(200)
    assert not bm1.is_set(200)
    assert bm1.get_set_bits() == [42, 100]
    assert bm2.get_set_bits() == [42, 100, 200]


def test_is_set_boundaries():
    """Test is_set at element boundaries."""
    bm = Bitmask.create()

    # Test around 64-bit boundaries
    bm.set_bit(62)
    bm.set_bit(63)
    bm.set_bit(64)
    bm.set_bit(65)

    assert bm.is_set(62)
    assert bm.is_set(63)
    assert bm.is_set(64)
    assert bm.is_set(65)
    assert not bm.is_set(61)
    assert not bm.is_set(66)

    # Test around 128-bit boundary
    bm.set_bit(127)
    bm.set_bit(128)

    assert bm.is_set(127)
    assert bm.is_set(128)
    assert not bm.is_set(126)
    assert not bm.is_set(129)
    assert bm.get_set_bits() == [62, 63, 64, 65, 127, 128]
