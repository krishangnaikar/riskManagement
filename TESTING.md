## Tests

```sh
python -m pip install -r requirements-test.txt
python -m pytest
```

These initial tests cover selected behavior with external services mocked. They do not establish full integration coverage.

Coverage: anonymous access redirects, login state, and logout. SQLAlchemy and the identity provider are mocked; database schema and CRUD integration remain untested.
