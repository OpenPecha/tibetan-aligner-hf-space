from github_utils import clone_repo, create_github_repo, repo_exists


def test_repo_exists():
    assert repo_exists("TM0731") == True
