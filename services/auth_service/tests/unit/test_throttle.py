from app import config
from app.utils.throttle import LoginThrottle


def test_locks_after_max_failures_for_same_ip_and_account():
    t = LoginThrottle()
    for _ in range(config.LOGIN_MAX_FAILURES):
        assert t.retry_after("1.1.1.1", "a@x.com") == 0
        t.record_failure("1.1.1.1", "a@x.com")
    assert t.retry_after("1.1.1.1", "a@x.com") > 0


def test_other_ip_is_not_locked_by_single_attacker():
    t = LoginThrottle()
    for _ in range(config.LOGIN_MAX_FAILURES):
        t.record_failure("1.1.1.1", "a@x.com")
    assert t.retry_after("2.2.2.2", "a@x.com") == 0


def test_account_key_is_case_insensitive():
    t = LoginThrottle()
    for _ in range(config.LOGIN_MAX_FAILURES):
        t.record_failure("1.1.1.1", "A@X.com")
    assert t.retry_after("1.1.1.1", "a@x.COM") > 0


def test_success_resets_ip_account_counter():
    t = LoginThrottle()
    for _ in range(config.LOGIN_MAX_FAILURES - 1):
        t.record_failure("1.1.1.1", "a@x.com")
    t.reset("1.1.1.1", "a@x.com")
    t.record_failure("1.1.1.1", "a@x.com")
    assert t.retry_after("1.1.1.1", "a@x.com") == 0


def test_distributed_attack_on_one_account_hits_account_limit():
    t = LoginThrottle()
    for i in range(config.LOGIN_MAX_FAILURES_PER_ACCOUNT):
        t.record_failure(f"10.0.{i // 250}.{i % 250}", "victim@x.com")
    assert t.retry_after("9.9.9.9", "victim@x.com") > 0
