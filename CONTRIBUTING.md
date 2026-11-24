# Contributing

Upload2Shell is a lab reproducer for a fixed interpreter CVE. Contributions
are welcome when they keep it safe and reproducible.

## Good contributions

- new distro variants (Ubuntu 26.04, Fedora, RHEL) with pinned vulnerable
  builds;
- better overlap reliability for long-lived workers;
- standalone IPP features (`--discover`, job polling, authentication modes);
- tests, documentation, and asset fixes.

## Not accepted

- live target lists, mass scanners, or "exploit all" features;
- destructive commands or persistence;
- real customer data, credentials, or production command output;
- changes that remove the loopback-first guard;
- claims of discovery that are not backed by the advisory/CVE.

## Development

```bash
python3 -m unittest discover -s tests -v
./fetch-debs.sh && docker build -t upload2shell-deb13 .
docker run --rm upload2shell-deb13 \
  gs -dSAFER -sDEVICE=nullpage -q /root/poc-native-write.pdf
```

## Security issues

Use the private reporting path in [SECURITY.md](SECURITY.md).
