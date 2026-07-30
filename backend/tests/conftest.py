# Re-export all fixtures centrally
pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.tenants",
    "tests.fixtures.users",
    "tests.fixtures.roles",
    "tests.fixtures.permissions",
    "tests.fixtures.auth"
]
