import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from buildgen.common.utils import UniqueList


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


class TestUniqueListPropertyBased:
    """Property-based tests for UniqueList using Hypothesis."""

    @given(st.lists(st.integers()))
    def test_uniqueness_invariant(self, items: list[int]):
        """All elements in UniqueList are unique."""
        ul = UniqueList(items)
        assert len(ul) == len(set(ul))

    @given(st.lists(st.integers()))
    def test_preserves_first_occurrence_order(self, items: list[int]):
        """First occurrences maintain their relative order."""
        ul = UniqueList(items)
        seen = []
        for item in items:
            if item not in seen:
                seen.append(item)
        assert list(ul) == seen

    @given(st.lists(st.integers()), st.integers())
    def test_add_idempotent(self, items: list[int], new_item: int):
        """Adding an existing element doesn't change the list."""
        ul = UniqueList(items)
        if new_item in ul:
            original = list(ul)
            ul.add(new_item)
            assert list(ul) == original

    @given(st.lists(st.integers()), st.integers())
    def test_add_preserves_uniqueness(self, items: list[int], new_item: int):
        """Adding any element maintains uniqueness invariant."""
        ul = UniqueList(items)
        ul.add(new_item)
        assert len(ul) == len(set(ul))
        assert new_item in ul

    @given(st.lists(st.integers()), st.integers())
    def test_append_preserves_uniqueness(self, items: list[int], new_item: int):
        """Appending any element maintains uniqueness invariant."""
        ul = UniqueList(items)
        ul.append(new_item)
        assert len(ul) == len(set(ul))
        assert new_item in ul

    @given(st.lists(st.integers()), st.lists(st.integers()))
    def test_extend_preserves_uniqueness(self, items1: list[int], items2: list[int]):
        """Extending maintains uniqueness invariant."""
        ul = UniqueList(items1)
        ul.extend(items2)
        assert len(ul) == len(set(ul))
        for item in items2:
            assert item in ul

    @given(st.lists(st.integers(), min_size=1), st.integers(min_value=0))
    def test_insert_preserves_uniqueness(self, items: list[int], idx: int):
        """Inserting maintains uniqueness invariant."""
        ul = UniqueList(items)
        new_item = max(items) + 1  # Ensure new unique item
        idx = idx % (len(ul) + 1)  # Valid index
        ul.insert(idx, new_item)
        assert len(ul) == len(set(ul))
        assert new_item in ul

    @given(st.lists(st.integers()), st.lists(st.integers()))
    def test_add_operator_preserves_uniqueness(self, items1: list[int], items2: list[int]):
        """+ operator maintains uniqueness invariant."""
        ul1 = UniqueList(items1)
        ul2 = UniqueList(items2)
        result = ul1 + ul2
        assert len(result) == len(set(result))
        for item in items1:
            assert item in result
        for item in items2:
            assert item in result

    @given(st.lists(st.integers()), st.lists(st.integers()))
    def test_iadd_operator_preserves_uniqueness(self, items1: list[int], items2: list[int]):
        """+= operator maintains uniqueness invariant."""
        ul = UniqueList(items1)
        ul += items2
        assert len(ul) == len(set(ul))
        for item in items1:
            assert item in ul
        for item in items2:
            assert item in ul

    @given(st.lists(st.integers()))
    def test_length_equals_unique_count(self, items: list[int]):
        """Length equals number of unique elements in input."""
        ul = UniqueList(items)
        assert len(ul) == len(set(items))

    @given(st.lists(st.integers(), min_size=1))
    def test_first_and_last_are_elements(self, items: list[int]):
        """first() and last() return elements from the list."""
        ul = UniqueList(items)
        assert ul.first() in ul
        assert ul.last() in ul
        assert ul.first() == ul[0]
        assert ul.last() == ul[-1]

    @given(st.lists(st.integers()))
    def test_membership_consistent_with_set(self, items: list[int]):
        """Membership testing is consistent with set membership."""
        ul = UniqueList(items)
        item_set = set(items)
        for item in items:
            assert (item in ul) == (item in item_set)
        # Test some items not in list
        for i in range(-10, 10):
            assert (i in ul) == (i in item_set)

    @given(st.lists(st.integers()))
    def test_iteration_yields_all_unique_elements(self, items: list[int]):
        """Iteration yields exactly the unique elements."""
        ul = UniqueList(items)
        iterated = list(ul)
        assert len(iterated) == len(set(items))
        assert set(iterated) == set(items)

    @given(st.lists(st.text(min_size=1, max_size=10)))
    def test_works_with_strings(self, items: list[str]):
        """UniqueList works correctly with string elements."""
        ul = UniqueList(items)
        assert len(ul) == len(set(items))
        for item in items:
            assert item in ul

    @given(st.lists(st.tuples(st.integers(), st.integers())))
    def test_works_with_tuples(self, items: list[tuple[int, int]]):
        """UniqueList works correctly with tuple elements."""
        ul = UniqueList(items)
        assert len(ul) == len(set(items))
        for item in items:
            assert item in ul

    @given(st.lists(st.integers(), min_size=1))
    @settings(max_examples=50)
    def test_slicing_preserves_order(self, items: list[int]):
        """Slicing preserves element order."""
        ul = UniqueList(items)
        if len(ul) >= 2:
            sliced = ul[1:]
            assert list(sliced) == list(ul)[1:]

    @given(st.lists(st.integers(), min_size=1))
    def test_index_finds_correct_position(self, items: list[int]):
        """index() returns correct position for each element."""
        ul = UniqueList(items)
        for i, item in enumerate(ul):
            assert ul.index(item) == i
