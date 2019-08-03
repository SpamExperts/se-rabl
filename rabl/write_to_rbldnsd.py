#! /usr/bin/env python

"""Reactive Autonomous Blackhole List Server

General a zone file suitable for use with rbldnsd from the
data collected by the RABL server.
"""

from __future__ import absolute_import

import os
import shutil
import hashlib
import logging
import optparse
import datetime
import tempfile
import configparser

import psutil

import MySQLdb

import rabl.common


def load_configuration():
    """Load server-specific configuration settings."""
    conf = configparser.ConfigParser()
    defaults = {
        "mysql": {
            "host": "localhost",
            "db": "",
            "user": "rabl",
            "password": "",
        },
        "sentry": {
            "dsn": "",
        },
    }
    # Load in default values.
    for section, values in defaults.items():
        conf.add_section(section)
        for option, value in values.items():
            conf.set(section, option, value)
    if os.path.exists("/etc/rabl.conf"):
        # Overwrite with local values.
        conf.read("/etc/rabl.conf")
    return conf


CONF = load_configuration()


def get_temporary_location(filename):
    """Return an appropriate temporary location to store the file.
    
    We use a temp folder within the final destination so that the copy
    should be atomic and so that we're using the same disk (e.g. taking
    advantage of the same speed, etc).
    """
    tmp_folder = os.path.join(os.path.dirname(filename), "tmp")
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    fd, tempname = tempfile.mkstemp(os.path.basename(filename),
                                    dir=tmp_folder)
    os.close(fd)
    return tempname


def write_zone(filename, table_name, life, minspread):
    """Output a rbldnsd zone file.

    Also handles expiry."""
    logger = logging.getLogger("rabl")
    # We write to a temporary file and then do an atomic move to the correct
    # name, so that if something is currently accessing the file we never
    # have it truncated.
    tempname = get_temporary_location(filename)
    logger.debug("Writing list to %s", tempname)
    with open(tempname, "w") as fout:
        # 127.0.0.2 is always spam (this is the test address).
        total = 1
        fout.write("127.0.0.2\n")
        # XXX This doesn't work properly at the moment.  The lists are
        # XXX configured as ip4tset, which means that these are IP addresses
        # XXX in natural format, but we are mixing that with "generic", which
        # XXX is hostnames (for the IPv6) addresses.  We need to make them
        # XXX all "generic", which means reversing the IPv4 addresses, or
        # XXX split the IPv4 and IPv6 into two separate lists.
#        fout.write("2.0.0.0.0.0.f.7.f.f.f.f."
#                   "0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0\n")
#        total += 1
        db = MySQLdb.connect(host=CONF.get("mysql", "host"),
                             user=CONF.get("mysql", "user"),
                             passwd=CONF.get("mysql", "password"),
                             db=CONF.get("mysql", "db"),
                             connect_timeout=60)
        c = db.cursor()
        # Expire the old data.
        c.execute("DELETE FROM `%s` WHERE spam_count < 1 OR last_seen < %%s" %
                  table_name, (datetime.datetime.now() -
                               datetime.timedelta(seconds=life),))
        db.commit()
        c.execute("SELECT ip FROM `%s` GROUP BY ip HAVING COUNT(*) > %%s" %
                  table_name, (minspread,))
        for row in c.fetchall():
            ip = row[0]
            if ip in ("127.0.0.1", "0.0.0.0", "::1"):
                # These are permanently whitelisted.
                continue
            if ":" in ip:
                # XXX These do not work properly at the moment; see above.
                continue
            fout.write(ip)
            fout.write("\n")
            total += 1
        c.close()
        db.close()
    # Rename to the final location - the OS should ensure that this is
    # atomic.
    shutil.move(tempname, filename)
    generate_checksum(filename)
    logger.info("Wrote %s blacklisted addresses to zone file.", total)


def generate_checksum(filename):
    """Generate a SHA256 hash checksum for the file."""
    with open(filename + ".sha256", "wb") as sha_sig:
        with open(filename, "rb") as file_content:
            sha256_hash = hashlib.sha256()
            while True:
                chunk = file_content.read(1024 * 1024)
                if not chunk:
                    break
                sha256_hash.update(chunk)
            sha256_hash = sha256_hash.hexdigest()
        sha_sig.write("%s %s\n" % (os.path.basename(filename), sha256_hash))


def main():
    """Parse command-line options and execute requested actions."""
    description = "Reactive Autonomous Black List"
    opt = optparse.OptionParser(description=description)
    opt.add_option("-n", "--nice", dest="nice", type="int",
                   help="'nice' level", default=0)
    opt.add_option("-i", "--ionice", dest="ionice", type="int",
                   help="'ionice' level, can be one of this 0,1,2,3")
    opt.add_option("--ionice-prio", dest="ionice_prio", type="int",
                   help="'ionice' class priority, this goes from 0 to 7 on "
                   "ionice class 1 and 2")
    opt.add_option("--list", dest="table_name",
                   help="name of list to output (rabl-automatic, "
                   "rabl-reported, rabl-verified)",
                   default="rabl-verified")
    opt.add_option("--zone-file", dest="zone_file",
                   help="filename for zone file", default="/tmp/rabl.zone")
    opt.add_option("--life", dest="life", type="int",
                   help="number of seconds entries live for", default=60)
    opt.add_option("--minspread", dest="minspread", type="int",
                   help="minimum number of reporters to be listed",
                   default=10000)
    opt.add_option("-d", "--debug", action="store_true", default=False,
                   dest="debug", help="enable debugging output")
    options = opt.parse_args()[0]
    os.nice(options.nice)
    if options.ionice is not None:
        proc = psutil.Process(os.getpid())
        proc.set_ionice(options.ionice, options.ionice_prio)

    logger = logging.getLogger("rabl")
    if options.debug:
        stream_level = "DEBUG"
    else:
        stream_level = "CRITICAL"
    rabl.common.setup_logging(logger, "/var/log/rabl.log",
                              CONF.get("sentry", "dsn"),
                              stream_level=stream_level)

    write_zone(options.zone_file, options.table_name, options.life,
               options.minspread)


if __name__ == "__main__":
    main()
