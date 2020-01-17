sed -i "" "s/name='resilient',/name='test-resilient',/g" resilient/setup.py
sed -i "" "s/name='resilient-lib',/name='test-resilient-lib',/g" resilient-lib/setup.py
sed -i "" "s/name='resilient-circuits',/name='test-resilient-circuits',/g" resilient-circuits/setup.py
sed -i "" "s/name='pytest_resilient_circuits',/name='test_pytest_resilient_circuits',/g" pytest-resilient-circuits/setup.py