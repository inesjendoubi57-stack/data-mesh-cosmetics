
import json
import pytest
from pathlib import Path

import validate_registry as validator


def create_valid_registry(tmp_path):
    """Create a temporary valid registry and YAML contract."""

    contract_dir = tmp_path / "contracts"
    contract_dir.mkdir()

    contract = {
        "name": "test-contract",
        "version": "1.0.0",
        "owner": "test-team",
        "description": "Test contract",
        "compatibility": "backward"
    }

    contract_file = contract_dir / "test-contract.yaml"

    import yaml
    contract_file.write_text(
        yaml.safe_dump(contract),
        encoding="utf-8"
    )

    registry = {
        "registry_version": "1.0",
        "path_convention": "repository_root",
        "contracts": [
            {
                "name": "test-contract",
                "domain": "Test",
                "owner": "test-team",
                "description": "Test contract",
                "current_version": "1.0.0",
                "compatibility": "backward",
                "versions": [
                    {
                        "version": "1.0.0",
                        "file_path": "contracts/test-contract.yaml",
                        "status": "active"
                    }
                ]
            }
        ]
    }

    registry_file = tmp_path / "registry.json"
    registry_file.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    return registry_file


@pytest.fixture
def temporary_registry(tmp_path, monkeypatch):
    registry_file = create_valid_registry(tmp_path)

    monkeypatch.setattr(
        validator,
        "ROOT_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        validator,
        "REGISTRY_PATH",
        registry_file
    )

    return registry_file


def test_valid_registry(temporary_registry):
    assert validator.validate_registry() is True
def test_missing_contract_file(temporary_registry, tmp_path):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    registry["contracts"][0]["versions"][0]["file_path"] = (
        "contracts/missing-contract.yaml"
    )

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_duplicate_contract_names(temporary_registry):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    duplicate_contract = registry["contracts"][0].copy()
    registry["contracts"].append(duplicate_contract)

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_invalid_version_format(temporary_registry):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    registry["contracts"][0]["current_version"] = "1.0"

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_path_traversal(temporary_registry):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    registry["contracts"][0]["versions"][0]["file_path"] = (
        "../outside-contract.yaml"
    )

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_owner_mismatch(temporary_registry, tmp_path):
    contract_file = tmp_path / "contracts" / "test-contract.yaml"

    import yaml
    contract = yaml.safe_load(contract_file.read_text(encoding="utf-8"))

    contract["owner"] = "another-team"

    contract_file.write_text(
        yaml.safe_dump(contract),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_description_mismatch(temporary_registry, tmp_path):
    contract_file = tmp_path / "contracts" / "test-contract.yaml"

    import yaml
    contract = yaml.safe_load(contract_file.read_text(encoding="utf-8"))

    contract["description"] = "Different description"

    contract_file.write_text(
        yaml.safe_dump(contract),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_compatibility_mismatch(temporary_registry, tmp_path):
    contract_file = tmp_path / "contracts" / "test-contract.yaml"

    import yaml
    contract = yaml.safe_load(contract_file.read_text(encoding="utf-8"))

    contract["compatibility"] = "forward"

    contract_file.write_text(
        yaml.safe_dump(contract),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_multiple_active_versions(temporary_registry):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    registry["contracts"][0]["versions"].append({
        "version": "1.1.0",
        "file_path": "contracts/test-contract.yaml",
        "status": "active"
    })

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_invalid_version_status(temporary_registry):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    registry["contracts"][0]["versions"][0]["status"] = "pending"

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_missing_required_field(temporary_registry):
    registry = json.loads(temporary_registry.read_text(encoding="utf-8"))

    del registry["contracts"][0]["owner"]

    temporary_registry.write_text(
        json.dumps(registry),
        encoding="utf-8"
    )

    assert validator.validate_registry() is False
def test_invalid_json(temporary_registry):
    temporary_registry.write_text(
        "{ invalid json content",
        encoding="utf-8"
    )

    assert validator.validate_registry() is False