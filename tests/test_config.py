import os
from unittest.mock import patch


def test_config_loads_from_env():
    env = {
        "GITHUB_TOKEN": "gh_test",
        "GITEE_TOKEN": "gitee_test",
        "TELEGRAM_BOT_TOKEN": "123:ABC",
        "TELEGRAM_CHAT_ID": "-100123",
    }
    with patch.dict(os.environ, env, clear=False):
        from importlib import reload
        import config
        reload(config)
        assert config.GITHUB_TOKEN == "gh_test"
        assert config.GITEE_TOKEN == "gitee_test"
        assert config.TELEGRAM_BOT_TOKEN == "123:ABC"
        assert config.TELEGRAM_CHAT_ID == "-100123"


def test_config_defaults():
    from importlib import reload
    import config
    reload(config)
    assert config.DB_PATH == "data/trending.db"
