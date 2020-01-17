sed -i "s/name='resilient',/name='test_resilient',/g" resilient/setup.py
sed -i "s/name='resilient_lib',/name='test_resilient_lib',/g" resilient-lib/setup.py
sed -i "s/name='resilient_circuits',/name='test_resilient_circuits',/g" resilient-circuits/setup.py
sed -i "s/name='pytest_resilient_circuits',/name='test_pytest_resilient_circuits',/g" pytest-resilient-circuits/setup.py