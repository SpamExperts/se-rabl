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
import sys
import time
import json
import shutil
import socket
import logging
import optparse
import datetime
import tempfile
import ConfigParser
import SocketServer

import ipaddr

import psutil

import MySQLdb

import raven
import raven.transport
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler


RABL_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS `%s` (
  `ip` char(43) NOT NULL COMMENT "The reported IP address or network",
  `reporter` char(43) NOT NULL COMMENT "The IP of the reporting user",
  `spam_count` int(11) default 0 COMMENT "The number of spam messages seen from this IP",
  `last_seen` timestamp COMMENT "Last time a spam message was seen from this IP by this user",
  PRIMARY KEY  (`ip`, `reporter`),
  KEY  (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT="Reactive Autonomous Blackhole List"
"""


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
        "rabl": {
            # Reports from this IP may specify the original source of the
            # report.
            "trusted_ip": "",
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


class RequestHandler(SocketServer.DatagramRequestHandler):
    """Handle a single request."""
    def handle(self):
        """Handle a single incoming connection."""
        logger = logging.getLogger("rabl")
        try:
            self._handle()
        except Exception as e:
            logger.error("Unable to handle report: %s", e)

    def _handle(self):
        """Handle a single incoming connection."""
        logger = logging.getLogger("rabl")
        logger.debug("Handling report from %s", self.client_address[0])
        packet = self.rfile.read(320000).strip()

        # claimed_reporter is an IP address when from the trusted IP, or ""
        # otherwise.
        address, is_spam, claimed_reporter = packet.strip().split(",")
        is_spam = is_spam.lower() == "true"

        # We change reported IPv6 addresses to the /64 network.
        address = ipaddr.IPAddress(address)
        if isinstance(address, ipaddr.IPv6Address):
            address = ipaddr.IPNetwork(str(address) + "/64").network
        reporter = ipaddr.IPAddress(self.client_address[0])

        if reporter == CONF.get("rabl", "trusted_ip"):
            table_name = "rabl-verified"
            # This IP is permitted to claim the report is from other IPs.
            reporter = ipaddr.IPAddress(claimed_reporter)
        # If the report has a claimed reporter, then this has been
        # reported by a human, so may be able to be trusted more.
        elif claimed_reporter:
            table_name = "rabl-reported"
        # Otherwise, this must be an automatic detection, and can't be
        # trusted.
        else:
            table_name = "rabl-automatic"
        # Calculate the change in count.
        if is_spam:
            diff = 1
        else:
            diff = -1
        self.update_database(table_name, address, reporter, diff, is_spam)

    def update_database(self, table_name, address, reporter, diff, is_spam):
        """Update the database with the specified report."""
        logger = logging.getLogger("rabl")
        # XXX It might be better to queue these and do them in a batch.
        try:
            db = MySQLdb.connect(host=CONF.get("mysql", "host"),
                                 user=CONF.get("mysql", "user"),
                                 passwd=CONF.get("mysql", "password"),
                                 db=CONF.get("mysql", "db"),
                                 connect_timeout=60)
        except MySQLdb.Error as e:
            logger.error("Unable to connect to database: %s", e)
            return
        c = db.cursor()
        # Note that this cannot work with executemany, because there is an
        # argument in the ON DUPLICATE KEY part.
        # The str(address) is necessary, because sqlite3 doesn't do an
        # automatic conversion to string.
        try:
            c.execute("INSERT INTO `%s` (ip, reporter, spam_count) VALUES "
                      "(%%s, %%s, %%s) ON DUPLICATE KEY UPDATE "
                      "spam_count=spam_count+%%s" % table_name,
                      (str(address), str(reporter), diff, diff))
        except MySQLdb.Error as e:
            logger.error("Unable to update RABL: %s", e)
        else:
            db.commit()
        c.close()
        db.close()
        logger.info("Address %s reported by %s (spam: %s)", address,
                    reporter, is_spam)


class RABLServer(SocketServer.UDPServer):
    """A simple server that handles RABL updates."""
    handler_class = RequestHandler

    def __init__(self, address):
        logger = logging.getLogger("rabl")
        logger.debug("Listening on %s", address)
        SocketServer.UDPServer.__init__(self, address, self.handler_class)


def write_zones(fmt, filename, template, table_name, debug=False):
    """Output a bind/rbldnsd zone file.

    Also handles expiry."""
    if fmt == "bind":
        fmt = lambda ip: "%s\t\tIN\tA\t127.0.0.2\n" % \
            (".".join(reversed(ip.split('.'))),)
    elif fmt == "rbldnsd":
        fmt = lambda ip: ip + "\n"
    else:
        assert False, "Unknown zone file format: %s" % fmt
    # We write to a temporary file and then do an atomic move to the correct
    # name, so that if something is currently accessing the file we never
    # have it truncated.
    fd, tempname = tempfile.mkstemp("rabl")
    os.close(fd)
    fout = open(tempname, "w")
    if template:
        if debug:
            print "Reading zone template from", template
        with open(template) as templatef:
            for line in templatef:
                line = line.replace("@serial@", str(int(time.time())))
                fout.write(line)
    # 127.0.0.2 is always spam (this is the test address).
    total = 2
    fout.write(fmt("127.0.0.2"))
    # XXX This doesn't work properly at the moment.  The lists are
    # XXX configured as ip4tset, which means that these are IP addresses in
    # XXX natural format, but we are mixing that with "generic", which is
    # XXX hostnames (for the IPv6) addresses.  We need to make them all
    # XXX "generic", which means reversing the IPv4 addresses, or split the
    # XXX IPv4 and IPv6 into two separate lists.
    fout.write(fmt("2.0.0.0.0.0.f.7.f.f.f.f."
                   "0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0"))
    db = MySQLdb.connect(host=CONF.get("mysql", "host"),
                         user=CONF.get("mysql", "user"),
                         passwd=CONF.get("mysql", "password"),
                         db=CONF.get("mysql", "db"),
                         connect_timeout=60)
    c = db.cursor()
    c.execute("DELETE FROM `%s` WHERE spam_count < 1 OR last_seen < %%s" %
              table_name, (datetime.datetime.now() -
                           datetime.timedelta(seconds=LIFE[table_name]),))
    db.commit()
    c.execute("SELECT ip FROM `%s` GROUP BY ip HAVING COUNT(*) > %%s" %
              table_name, (MINSPREAD[table_name],))
    for row in c.fetchall():
        ip = row[0]
        if ip in ("127.0.0.1", "0.0.0.0", "::1"):
            # These are permanently whitelisted.
            continue
        fout.write(fmt(ip))
        total += 1
    c.close()
    db.close()
    fout.close()
    # Rename to the final location - the OS should ensure that this is
    # atomic.
    shutil.move(tempname, filename)
    if debug:
        print "Wrote %s blacklisted addresses to zone file." % total


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
    opt.add_option("-p", "--port", dest="port", type="int",
                   help="port to listen on for UDP reports", default=61382)
    opt.add_option("--list", dest="table_name",
                   help="name of list to output (rabl-automatic, "
                   "rabl-reported, rabl-verified)",
                   default="rabl-verified")
    opt.add_option("--zone-file", dest="zone_file",
                   help="filename for zone file",
                   default="/var/lib/rbldns/se-rabl.spamrl.com")
    opt.add_option("--zone-template", dest="zone_template",
                   help="filename for zone template", default=None)
    opt.add_option("-d", "--debug", action="store_true", default=False,
                   dest="debug", help="enable debugging output")
    options = opt.parse_args()[0]
    os.nice(options.nice)
    if options.ionice is not None:
        proc = psutil.Process(os.getpid())
        proc.set_ionice(options.ionice, options.ionice_prio)

    if options.debug:
        print "Writing zone file in rblsdns format."
    write_zones("rbldnsd", options.zone_file, options.zone_template,
                options.table_name, debug=options.debug)

    logger = logging.getLogger("rabl")
    logger.setLevel(logging.DEBUG)
    if options.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
    else:
        daemonize(
            stdout="/var/log/rabl_server.out",
            pidfile="/var/run/rabl_server.pid",
            startmsg="%s")
        handler = logging.FileHandler(
            "/var/log/rabl_server.log")
        handler.setLevel(logging.WARNING)
    if CONF.get("sentry", "dsn"):
        client = raven.Client(CONF.get("sentry", "dsn"),
                              transport=raven.transport.HTTPTransport)
        sentry_handler = SentryHandler(client)
        sentry_handler.setLevel(logging.WARNING)
        logger.addHandler(sentry_handler)
        sentry_internal = logging.getLogger("sentry.errors")
        sentry_internal.addHandler(sentry_handler)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    server = RABLServer(("", options.port))
    server.serve_forever()


if __name__ == "__main__":
    main()
