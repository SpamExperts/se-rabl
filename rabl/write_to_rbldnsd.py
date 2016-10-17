#! /usr/bin/env python

"""Reactive Autonomous Blackhole List Server

The concept is based on the original rabl.nuclearelephant.com RABL, but
the code is completely independent (and not at all compatible).

Unfortunately, the original documentation for RABL is not available any
more, so cannot be linked to here.

Essentially, the concept is that this is a DNSBL that is:

 * Reactive: entries are added/removed in response to events
 * Autonomous: everything is automatic (no manual listing/de-listing)

Entries on the list automatically expire after no new reports have been
received for a period of time.

In order to be listed, the IP must have been reported as a spam source
by a set number of different reporters ('spread'). The intent is that
a large number of reports from a single source is not as important as
a small number of reports from many different sources.
"""

from __future__ import absolute_import

import os
import shutil
import logging
import optparse
import datetime
import tempfile
import ConfigParser

import psutil

import MySQLdb

import raven
import raven.transport
from raven.handlers.logging import SentryHandler


def load_configuration():
    """Load server-specific configuration settings."""
    conf = ConfigParser.ConfigParser()
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
    for section, values in defaults.iteritems():
        conf.add_section(section)
        for option, value in values.iteritems():
            conf.set(section, option, value)
    if os.path.exists("/etc/rabl.conf"):
        # Overwrite with local values.
        conf.read("/etc/rabl.conf")
    return conf


CONF = load_configuration()


def write_zone(filename, table_name, life, minspread):
    """Output a rbldnsd zone file.

    Also handles expiry."""
    logger = logging.getLogger("rabl")
    # We write to a temporary file and then do an atomic move to the correct
    # name, so that if something is currently accessing the file we never
    # have it truncated.
    fd, tempname = tempfile.mkstemp("rabl")
    os.close(fd)
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
    logger.info("Wrote %s blacklisted addresses to zone file.", total)


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
    write_zone(options.zone_file, options.table_name, options.life,
               options.minspread)


if __name__ == "__main__":
    main()
