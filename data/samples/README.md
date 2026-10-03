# Sample files

`esmi_format_fixture.csv` is a **synthetic format fixture, not real data**. It has the
"wide" layout (one row per location-day, one column per minute) that `data/load_esmi.py`
expects, with planted outages so the tests can check the outage statistics. Real ESMI
data must be downloaded manually; see the instructions at the top of `data/load_esmi.py`.
