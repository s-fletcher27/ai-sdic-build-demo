import demo_app


def test_package_imports():
    assert demo_app.__version__ == "0.1.0"
