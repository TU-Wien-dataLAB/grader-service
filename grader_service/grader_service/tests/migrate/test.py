import pytest
from grader_service.migrate.migrate import DB_URL_PATT, get_matching_config

@pytest.fixture
def valid_db_urls():
    return [
        "c.GraderService.db_url = 'postgresql://username:password@localhost:5432/mydatabase'",
        "c.GraderService.db_url = 'postgresql://user:pass@myhost:8888/mydb'",
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydatabase/subpath'",
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?sslmode=require&sslcert=/path/to/cert.pem'",
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?connect_timeout=10&application_name=MyApp'",
        "c.GraderService.db_url = 'sqlite:////path/to/database.db'",
        "c.GraderService.db_url = 'sqlite:///relative/path/database.db'",
        "c.GraderService.db_url = 'sqlite:///C:/path/to/database.db'",
        "c.GraderService.db_url = 'sqlite:///:memory:'",
        "c.GraderService.db_url = 'sqlite:///path/to/database.db?timeout=5000&mode=ro'",
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?dummy1=value1&dummy2=value2'",
        "c.GraderService.db_url = 'postgresql://%75%73%65%72:%70%61%73%73@localhost:5432/mydb'",
        "c.GraderService.db_url = 'postgresql://user:pass@[2001:db8:85a3::8a2e:370:7334]:5432/mydb'",
        "c.GraderService.db_url = 'sqlite:///path/to/database.db?param1=value1&param2=value2'",
        "c.GraderService.db_url = 'sqlite:///path/to/database.db?timeout=5000&mode=ro&param1=value1'",
        "c.GraderService.db_url = 'sqlite:///path/to/unicode_路径.db'",
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?param1=value1&param2=value2&param3=value3&param4=value4&param5=value5'"
    ]


@pytest.fixture
def invalid_db_urls():
    return [
        "c.GraderService.db_url = 'postgresql://user:password@localhost:5432/'",  # Missing database name
        "c.GraderService.db_url = 'sqlite://localhost/dbname'",  # Missing absolute path
        "c.GraderService.db_url = 'sqlite:///path/to/database'",  # Missing file extension
        "c.GraderService.db_url = 'postgresql:user:password@localhost:5432/mydatabase'",  # Missing double slashes after "postgresql:"
        "c.GraderService.db_url = 'sqlite:/path/to/database.db'",  # Missing triple slashes after "sqlite:"
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?invalid_param'",  # Invalid query parameter
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?param1=value1&'",  # Invalid query parameter syntax
        "c.GraderService.db_url = 'sqlite:///path/to/database.db?param1=value1&param2=value2&'",  # Invalid query parameter syntax
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?param1=value1&param2=value2&param3'",  # Invalid query parameter syntax
        "c.GraderService.db_url = 'sqlite://localhost/dbname?param1=value1&param2=value2'",  # Invalid query parameter syntax
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?param1=value1?param2=value2'",  # Duplicate query parameter separator
        "c.GraderService.db_url = 'sqlite://user:pass@localhost:5432/mydb'",  # Invalid scheme for SQLite
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?param1=value1&param2=value2&param3=value3&param4=value4&param5=value5&'",  # Invalid query parameter syntax
        "c.GraderService.db_url = 'sqlite:///path/to/database.db?param1=value1&&param2=value2'",  # Duplicate query parameter separator
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?param1=value1&param2=value2&param3=value3&&param4=value4'",  # Duplicate query parameter separator
        "c.GraderService.db_url = 'sqlite://user:pass@localhost:5432/mydb?param1=value1&param2=value2&param3='",  # Invalid query parameter syntax
        "c.GraderService.db_url = 'postgresql://user:pass@localhost:5432/mydb?'",  # Empty query parameter
        "c.GraderService.db_url = 'sqlite:///path/to/database.db?'",  # Empty query parameter
    ]


def test_db_url_regex_matches_expected(valid_db_urls):
    "Checks that the regex matches the expected URLs"
    for url in valid_db_urls:
        assert get_matching_config(url, DB_URL_PATT) is not None

