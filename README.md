# Open Surplus Manager

## Run

```bash
pip install -r requirements.txt
```
  
```bash
python -m opensurplusmanager
```

## TODOs

- [ ] Simulators
- [ ] Better catching of exceptions
- [ ] Better logging
- [ ] Protect some attributes from being changed from core
- [ ] Maybe setup integrations via config.yaml instead of looking for all the folders in the integrations folder
- [ ] Docstrings
- [ ] aiohttp Don’t create a session per request. Most likely you need a session per application which performs all requests together.
