# Contributing

Upload2Shell is a lab reproducer for an already-fixed interpreter bug. If you
want to send something, keep it safe and keep it reproducible.

## Things I will happily take

- more distro variants (26.04, Fedora, RHEL) with pinned vulnerable builds
- better odds on the overlap for workers that have been up a while
- client features that stay local: `--discover`, job polling, auth modes
- tests, docs, and asset fixes

## Things I will turn down

- target lists, mass scanners, "exploit everything" switches
- destructive commands, or any kind of persistence
- real customer data, credentials, or production output
- anything that drops the loopback-first guard
- discovery claims with no advisory behind them

## Working on it

```bash
python3 -m unittest discover -s tests -v

./fetch-debs.sh && docker build -t upload2shell-deb13 .
docker run --rm --entrypoint gs upload2shell-deb13 \
  -dSAFER -sDEVICE=nullpage -q /root/poc-native-write.pdf
```

## Security

For anything sensitive, use the private path in [SECURITY.md](SECURITY.md).
