
import subprocess

import pytest
import yaml

import check_contract_changes as gate


CONTRACT = {
    "name": "test-contract",
    "version": "1.0.0",
    "schema": [
        {"name": "product_id", "type": "string", "required": True},
        {"name": "price", "type": "float", "required": True},
    ],
    "invariants": ["price > 0"],
    "sla": {"freshness_max_minutes": 60},
}


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@test", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    contracts = tmp_path / "contracts"
    contracts.mkdir()
    (contracts / "test-contract.yaml").write_text(yaml.safe_dump(CONTRACT))

    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "contract v1")

    monkeypatch.setattr(gate, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(gate, "CONTRACTS_DIR", contracts)
    monkeypatch.setenv("BASE_REF", "main")

    return tmp_path


def write_contract(repo, contract):
    (repo / "contracts" / "test-contract.yaml").write_text(yaml.safe_dump(contract))


def test_unchanged_contract_passes(repo):
    assert gate.main() == 0


def test_renamed_field_is_blocked(repo):
    contract = yaml.safe_load(yaml.safe_dump(CONTRACT))
    contract["schema"][1]["name"] = "unit_price"
    write_contract(repo, contract)

    assert gate.main() == 1


def test_type_change_is_blocked(repo):
    contract = yaml.safe_load(yaml.safe_dump(CONTRACT))
    contract["schema"][1]["type"] = "string"
    write_contract(repo, contract)

    assert gate.main() == 1


def test_optional_field_added_passes(repo):
    contract = yaml.safe_load(yaml.safe_dump(CONTRACT))
    contract["schema"].append({"name": "image_url", "type": "string", "required": False})
    write_contract(repo, contract)

    assert gate.main() == 0


def test_new_contract_file_passes(repo):
    (repo / "contracts" / "another-contract.yaml").write_text(yaml.safe_dump(CONTRACT))

    assert gate.main() == 0


def test_unknown_base_branch_fails(repo, monkeypatch):
    monkeypatch.setenv("BASE_REF", "does-not-exist")

    assert gate.main() == 1
