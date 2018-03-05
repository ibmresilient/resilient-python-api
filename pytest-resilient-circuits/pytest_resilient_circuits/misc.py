""" Test utilities for Resilient """


def verify_subset(expected, actual):
    """Test that the values match, where expected can be a subset of actual"""
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        for (key, value) in expected.items():
            verify_subset(value, actual.get(key))
    elif isinstance(expected, list):
        assert isinstance(actual, list)
        for evalue, avalue in zip(expected, actual):
            verify_subset(evalue, avalue)
    else:
        assert expected == actual
