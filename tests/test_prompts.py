from analyzer.prompts import load_prompt


def test_load_prompt_classify():
    prompt = load_prompt("classify", projects="[test]")
    assert "[test]" in prompt
    assert "technology domain" in prompt


def test_load_prompt_analyze():
    prompt = load_prompt("analyze", title="test/repo", url="http://test",
                         description="desc", language="Python",
                         stars_today="100", raw_content="readme")
    assert "test/repo" in prompt
    assert "Python" in prompt
