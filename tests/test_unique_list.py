import pytest
from buildgen import UniqueList


class TestUniqueList:
    """Test UniqueList data structure"""

    def test_unique_list_creation(self):
        """Test UniqueList creation and deduplication"""
        ul = UniqueList([1, 2, 3, 2, 4, 1, 5])
        assert list(ul) == [1, 2, 3, 4, 5]

    def test_unique_list_add(self):
        """Test adding elements to UniqueList"""
        ul = UniqueList([1, 2, 3])
        ul.add(4)
        ul.add(2)  # Won't be added again
        assert list(ul) == [1, 2, 3, 4]

    def test_unique_list_append(self):
        """Test appending elements to UniqueList"""
        ul = UniqueList([1, 2, 3])
        ul.append(4)
        ul.append(1)  # Won't be added again
        assert list(ul) == [1, 2, 3, 4]

    def test_unique_list_operations(self):
        """Test list operations on UniqueList"""
        ul = UniqueList([1, 2, 3, 4, 5])
        assert len(ul) == 5
        assert 3 in ul
        assert 6 not in ul
        assert ul.index(3) == 2
        assert ul.first() == 1
        assert ul.last() == 5

    def test_unique_list_slicing(self):
        """Test slicing operations on UniqueList"""
        ul = UniqueList([1, 2, 3, 4, 5])
        first_three = ul[:3]
        assert list(first_three) == [1, 2, 3]


class TestUniqueListDetailed:
    """Detailed tests for UniqueList data structure"""

    def test_unique_list_creation_empty(self):
        """Test creating empty UniqueList"""
        ul = UniqueList()
        assert len(ul) == 0
        assert list(ul) == []

    def test_unique_list_creation_with_duplicates(self):
        """Test creating UniqueList with duplicates"""
        ul = UniqueList([1, 2, 3, 2, 4, 1, 5])
        assert list(ul) == [1, 2, 3, 4, 5]  # Duplicates should be removed
        assert len(ul) == 5

    def test_unique_list_creation_with_strings(self):
        """Test UniqueList with string elements"""
        ul = UniqueList(["apple", "banana", "apple", "cherry", "banana"])
        assert list(ul) == ["apple", "banana", "cherry"]
        assert len(ul) == 3

    def test_add_elements(self):
        """Test adding elements to UniqueList"""
        ul = UniqueList([1, 2, 3])
        ul.add(4)
        ul.add(3)  # Won't be added again
        ul.add(5)
        assert list(ul) == [1, 2, 3, 4, 5]
        assert len(ul) == 5

    def test_append_elements(self):
        """Test appending elements to UniqueList"""
        ul = UniqueList([1, 2, 3])
        ul.append(4)
        ul.append(1)  # Won't be added again
        ul.append(5)
        assert list(ul) == [1, 2, 3, 4, 5]
        assert len(ul) == 5

    def test_extend_functionality(self):
        """Test extending UniqueList with multiple elements"""
        ul = UniqueList([1, 2, 3])
        ul.extend([4, 5, 3, 6, 2])  # 3 and 2 are duplicates
        assert list(ul) == [1, 2, 3, 4, 5, 6]
        assert len(ul) == 6

    def test_membership_testing(self):
        """Test 'in' operator with UniqueList"""
        ul = UniqueList([1, 2, 3, 4, 5])
        assert 3 in ul
        assert 6 not in ul
        assert 1 in ul
        assert 5 in ul

    def test_indexing_and_slicing(self):
        """Test indexing and slicing operations"""
        ul = UniqueList([1, 2, 3, 4, 5])

        # Test indexing
        assert ul[0] == 1
        assert ul[-1] == 5
        assert ul[2] == 3

        # Test slicing
        assert list(ul[1:4]) == [2, 3, 4]
        assert list(ul[:3]) == [1, 2, 3]
        assert list(ul[2:]) == [3, 4, 5]

    def test_index_method(self):
        """Test index method"""
        ul = UniqueList([1, 2, 3, 4, 5])
        assert ul.index(1) == 0
        assert ul.index(3) == 2
        assert ul.index(5) == 4

        with pytest.raises(ValueError):
            ul.index(10)  # Element not in list

    def test_first_last_methods(self):
        """Test first() and last() methods"""
        ul = UniqueList([10, 20, 30, 40, 50])
        assert ul.first() == 10
        assert ul.last() == 50

        # Test with single element
        ul_single = UniqueList([42])
        assert ul_single.first() == 42
        assert ul_single.last() == 42

    def test_first_last_empty_list(self):
        """Test first() and last() on empty list"""
        ul = UniqueList()
        with pytest.raises(IndexError):
            ul.first()
        with pytest.raises(IndexError):
            ul.last()

    def test_iteration(self):
        """Test iteration over UniqueList"""
        ul = UniqueList([1, 2, 3, 4, 5])
        result = []
        for item in ul:
            result.append(item)
        assert result == [1, 2, 3, 4, 5]

    def test_len_function(self):
        """Test len() function with UniqueList"""
        ul = UniqueList([1, 2, 3, 2, 4, 1, 5])
        assert len(ul) == 5  # After deduplication

        ul_empty = UniqueList()
        assert len(ul_empty) == 0

    def test_remove_method(self):
        """Test remove method if it exists"""
        ul = UniqueList([1, 2, 3, 4, 5])
        if hasattr(ul, "remove"):
            ul.remove(3)
            assert 3 not in ul
            assert list(ul) == [1, 2, 4, 5]

    def test_pop_method(self):
        """Test pop method if it exists"""
        ul = UniqueList([1, 2, 3, 4, 5])
        if hasattr(ul, "pop"):
            popped = ul.pop()
            assert popped == 5
            assert list(ul) == [1, 2, 3, 4]

    def test_clear_method(self):
        """Test clear method if it exists"""
        ul = UniqueList([1, 2, 3, 4, 5])
        if hasattr(ul, "clear"):
            ul.clear()
            assert len(ul) == 0
            assert list(ul) == []

    def test_set_operations(self):
        """Test set-like operations"""
        ul1 = UniqueList([1, 2, 3, 4, 5])
        ul2 = UniqueList([4, 5, 6, 7, 8])

        # Convert to sets for testing set operations
        set1 = set(ul1)
        set2 = set(ul2)

        # Union
        union_result = set1.union(set2)
        assert union_result == {1, 2, 3, 4, 5, 6, 7, 8}

        # Intersection
        intersection_result = set1.intersection(set2)
        assert intersection_result == {4, 5}

        # Difference
        difference_result = set1.difference(set2)
        assert difference_result == {1, 2, 3}

        # Symmetric difference
        symmetric_diff_result = set1.symmetric_difference(set2)
        assert symmetric_diff_result == {1, 2, 3, 6, 7, 8}

    def test_order_preservation(self):
        """Test that UniqueList preserves insertion order"""
        ul = UniqueList()
        ul.add("first")
        ul.add("second")
        ul.add("third")
        ul.add("second")  # Duplicate, should not change order
        ul.add("fourth")

        assert list(ul) == ["first", "second", "third", "fourth"]

    def test_equality_comparison(self):
        """Test equality comparison if supported"""
        ul1 = UniqueList([1, 2, 3])
        ul2 = UniqueList([1, 2, 3])
        ul3 = UniqueList([1, 2, 3, 4])

        # Note: This test depends on whether UniqueList implements __eq__
        if hasattr(ul1, "__eq__"):
            assert ul1 == ul2
            assert ul1 != ul3

    def test_string_representation(self):
        """Test string representation"""
        ul = UniqueList([1, 2, 3])
        str_repr = str(ul)
        # Just check that it doesn't crash and returns a string
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_with_complex_objects(self):
        """Test UniqueList with more complex objects"""

        class TestObj:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return isinstance(other, TestObj) and self.value == other.value

            def __hash__(self):
                return hash(self.value)

        obj1 = TestObj("a")
        obj2 = TestObj("b")
        obj3 = TestObj("a")  # Equal to obj1

        ul = UniqueList([obj1, obj2, obj3])
        # Should have only 2 elements since obj1 and obj3 are equal
        assert len(ul) == 2
        assert obj1 in ul
        assert obj2 in ul


# Legacy test function for backward compatibility
def test_unique_list():
    """Legacy test function matching the original test"""
    # Create a UniqueList
    ul = UniqueList([1, 2, 3, 2, 4, 1, 5])
    assert list(ul) == [1, 2, 3, 4, 5]  # Duplicates should be removed

    # Add elements
    ul.add(6)
    ul.add(3)  # Won't be added again
    assert list(ul) == [1, 2, 3, 4, 5, 6]

    # Use append (maintains uniqueness)
    ul.append(7)
    ul.append(1)  # Won't be added again
    assert list(ul) == [1, 2, 3, 4, 5, 6, 7]

    # Set operations
    ul2 = UniqueList([4, 5, 6, 7, 8])
    assert list(ul2) == [4, 5, 6, 7, 8]

    union_result = set(ul).union(ul2)
    assert union_result == {1, 2, 3, 4, 5, 6, 7, 8}

    intersection_result = set(ul).intersection(ul2)
    assert intersection_result == {4, 5, 6, 7}

    difference_result = set(ul).difference(ul2)
    assert difference_result == {1, 2, 3}

    symmetric_diff_result = set(ul).symmetric_difference(ul2)
    assert symmetric_diff_result == {1, 2, 3, 8}

    # First and last elements
    assert ul.first() == 1
    assert ul.last() == 7

    # Works with standard list operations
    assert len(ul) == 7
    assert 3 in ul
    assert 4 in ul
    assert ul.index(3) == 2  # 3 should be at index 2

    # Slicing works too
    first_three = ul[:3]
    assert list(first_three) == [1, 2, 3]
