from pathlib import Path

def test_no_root_acmf_stub_or_php_index():
    root=Path(__file__).resolve().parents[1]
    assert not (root/'acmf').exists()
    assert not (root/'index.php').exists()
    assert not (root/'acmf_core.py').exists()
    assert not (root/'acmf_solver.py').exists()

def test_manifest_is_current_enough():
    root=Path(__file__).resolve().parents[1]
    manifest=(root/'MANIFEST.txt').read_text(encoding='utf-8')
    assert 'src/acmf/core.py' in manifest
    assert 'main.py' in manifest
    assert 'README_DEPLOY.md' in manifest
    assert 'data/world_data_1995_2025.csv' in manifest
