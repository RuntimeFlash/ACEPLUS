from __future__ import annotations

from index import create_app


def test_legacy_route_contract_paths_exist() -> None:
    app = create_app()
    registered_paths = {route.path for route in app.routes}

    expected_paths = {
        "/api/tests",
        "/api/generate_test",
        "/api/create_test",
        "/api/subject_stats/{subject}",
        "/api/report",
        "/api/students_by_standard",
        "/api/upload_files",
        "/api/upload_images",
        "/api/uploads/{filename}",
        "/api/generate_from_files",
        "/api/generate_from_images",
        "/api/generate_hint",
        "/api/generate_solution",
    }

    missing = sorted(expected_paths - registered_paths)
    assert not missing, f"Missing legacy compatibility routes: {missing}"
