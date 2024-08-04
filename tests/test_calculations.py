from src.calculations import validate_inputs, calculate_weights, calculate_buy_plan
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_validate_inputs():
    # 测试有效输入
    validate_inputs(50000, 100, 90, 10, 0)

    # 测试无效输入
    with pytest.raises(ValueError):
        validate_inputs(-1000, 100, 90, 10, 0)  # 负资金
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 110, 10, 0)  # 止损价高于初始价
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 90, 101, 0)  # 网格数量过多


def test_calculate_weights():
    prices = [100, 95, 90, 85, 80]

    # 测试等金额分配
    weights_equal = calculate_weights(prices, 0, 100)
    assert len(weights_equal) == len(prices)
    assert all(w > 0 for w in weights_equal)

    # 测试指数分配
    weights_exp = calculate_weights(prices, 1, 100)
    assert len(weights_exp) == len(prices)
    assert all(w > 0 for w in weights_exp)
    assert weights_exp[-1] > weights_exp[0]  # 最低价格应该有最高权重

    # 测试线性分配
    weights_linear = calculate_weights(prices, 2, 100)
    assert len(weights_linear) == len(prices)
    assert all(w > 0 for w in weights_linear)
    assert weights_linear[-1] > weights_linear[0]  # 最低价格应该有最高权重


def test_calculate_buy_plan():
    funds = 50000
    initial_price = 100
    stop_loss_price = 90
    num_grids = 10
    allocation_method = 0

    buy_plan, warning = calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids, allocation_method)

    assert len(buy_plan) == num_grids
    assert all(price >= stop_loss_price and price <= initial_price for price, _ in buy_plan)
    assert all(quantity > 0 for _, quantity in buy_plan)
    assert sum(price * quantity for price, quantity in buy_plan) <= funds


def test_validate_inputs_edge_cases():
    # 测试边界值
    validate_inputs(1, 1, 0.1, 2, 0)  # 最小可能的有效输入

    # 测试更多无效输入
    with pytest.raises(ValueError):
        validate_inputs(50000, 0, 90, 10, 0)  # 初始价格为0
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 0, 10, 0)  # 止损价格为0
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 90, 0, 0)  # 网格数量为0
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 90, 10, 3)  # 无效的分配方式


def test_calculate_weights_edge_cases():
    # 测试单一价格
    assert calculate_weights([100], 0, 100) == [100]
    assert calculate_weights([100], 1, 100) == [100]
    assert calculate_weights([100], 2, 100) == [100]

    # 测试极端价格差
    prices_extreme = [1000, 1]
    weights_extreme = calculate_weights(prices_extreme, 1, 100)
    assert weights_extreme[1] > weights_extreme[0] * 10  # 确保最低价格的权重显著更高

    # 测试大量价格点
    prices_many = list(range(1, 101))  # 100个价格点
    weights_many = calculate_weights(prices_many, 2, 1000)
    assert len(weights_many) == 100
    assert weights_many[-1] == max(weights_many)  # 最低价格应有最高权重


def test_calculate_buy_plan_different_allocations():
    funds = 50000
    initial_price = 100
    stop_loss_price = 90
    num_grids = 10

    # 测试不同的分配方式
    for allocation_method in [0, 1, 2]:
        buy_plan, warning = calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids, allocation_method)
        assert len(buy_plan) == num_grids
        assert all(price >= stop_loss_price and price <= initial_price for price, _ in buy_plan)
        assert all(quantity > 0 for _, quantity in buy_plan)
        assert sum(price * quantity for price, quantity in buy_plan) <= funds


def test_calculate_buy_plan_edge_cases():
    # 测试极小资金
    buy_plan, warning = calculate_buy_plan(100, 10, 9, 5, 0)
    assert len(buy_plan) == 5
    assert sum(quantity for _, quantity in buy_plan) >= 10  # 至少应该买10股

    # 测试极大网格数
    buy_plan, warning = calculate_buy_plan(1000000, 100, 50, 100, 1)
    assert len(buy_plan) == 100

    # 测试初始价格和止损价格非常接近的情况
    buy_plan, warning = calculate_buy_plan(10000, 100, 99.9, 10, 2)
    assert len(buy_plan) == 10
    assert all(99.9 <= price <= 100 for price, _ in buy_plan)


def test_calculate_buy_plan_warnings():
    # 测试可能触发警告的情况
    _, warning = calculate_buy_plan(1000, 100, 90, 20, 0)
    assert "警告" in warning  # 资金可能不足以合理分配到所有网格

    _, warning = calculate_buy_plan(1000000, 100, 90, 2, 0)
    assert warning == ""  # 不应该有警告

# 添加更多测试...


if __name__ == "__main__":
    pytest.main()
