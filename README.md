Run:
```shell
cp .env.example .env
# fill in variables

uv run main.py
# (or) python main.py
```

Access the KV:
```shell
task user:create
USER_ID=<user_id> task user:download > $CREDS/cloud/idaho-mfg.creds

# test it out
nats --context=idaho-mfg kv get IDAHO_MFG everything
```

### Links
- https://connect.idmfg.org/home
- https://lunrjs.com/guides/searching.html
