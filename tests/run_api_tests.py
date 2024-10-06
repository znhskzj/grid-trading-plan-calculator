import unittest

def run_api_tests():
    # 发现并运行所有 API 相关的测试
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*_adapter.py')
    test_suite.addTest(test_loader.loadTestsFromName('tests.test_api_manager'))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return result

if __name__ == '__main__':
    run_api_tests()