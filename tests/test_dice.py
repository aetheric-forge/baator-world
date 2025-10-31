from baator.interface import PythonRNG
from baator.kernel import roll_expr, expr_adv, expr_dis

def test_roll_expr_bounds():
    rng = PythonRNG()
    for _ in range(200):
        v = roll_expr("3d6+2", rng)
        assert 5 <= v <= 20

def test_adv_dis():
    rng = PythonRNG()
    adv, dis = [], []
    for _ in range(5000):
        a = roll_expr(expr_adv(20), rng)
        d = roll_expr(expr_adv(20), rng)
        assert 1 <= a <= 20
        assert 1 <= d <= 20
        adv.append(a)
        dis.append(d)

    assert sum(adv) / len(adv) > sum(dis) / len(dis)

