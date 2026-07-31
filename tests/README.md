# Test layout

Default `pytest -q` runs the fast/local suite only. Slow scientific checks are marked `slow` and excluded by `pytest.ini`.

The `test_v2_*` files are retained as historical package/report compatibility artifacts. They currently do not define executable pytest functions and should not be treated as green scientific validation.

Run heavy checks explicitly:

```bash
pytest -q -m slow --override-ini='addopts='
```
