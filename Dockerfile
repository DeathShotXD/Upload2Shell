FROM debian:13

ARG DEBIAN_FRONTEND=noninteractive

# Dependencies first (from trixie), then downgrade to the vulnerable build.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ghostscript cups cups-client cups-filters python3 \
 && rm -rf /var/lib/apt/lists/*

COPY debs/ /tmp/debs/
RUN dpkg -i /tmp/debs/*.deb \
 && apt-mark hold ghostscript libgs10 libgs10-common \
 && rm -rf /tmp/debs

COPY lab/u2s.ppd /etc/cups/u2s.ppd
COPY lab/cupsd.conf /etc/cups/cupsd.conf
COPY lab/entrypoint.sh /entrypoint.sh
COPY poc-pipe.ps /root/poc-pipe.ps
COPY poc-native-write.pdf /root/poc-native-write.pdf
COPY cups_poc.py /root/cups_poc.py

RUN chmod +x /entrypoint.sh

EXPOSE 631
ENTRYPOINT ["/entrypoint.sh"]
