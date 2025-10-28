def test_imports():
    import baator
    from baator.kernel import Id, Event
    assert Id is not None
    assert Event is not None
