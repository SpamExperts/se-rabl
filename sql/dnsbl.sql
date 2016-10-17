CREATE TABLE IF NOT EXISTS `rabl-verified` (
  `ip` char(43) NOT NULL COMMENT "The reported IP address or network",
  `reporter` char(43) NOT NULL COMMENT "The IP of the reporting user",
  `spam_count` int(11) default 0 COMMENT "The number of spam messages seen from this IP",
  `last_seen` timestamp COMMENT "Last time a spam message was seen from this IP by this user",
  PRIMARY KEY  (`ip`, `reporter`),
  KEY  (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT="Reactive Autonomous Blackhole List"

CREATE TABLE IF NOT EXISTS `rabl-reported` (
  `ip` char(43) NOT NULL COMMENT "The reported IP address or network",
  `reporter` char(43) NOT NULL COMMENT "The IP of the reporting user",
  `spam_count` int(11) default 0 COMMENT "The number of spam messages seen from this IP",
  `last_seen` timestamp COMMENT "Last time a spam message was seen from this IP by this user",
  PRIMARY KEY  (`ip`, `reporter`),
  KEY  (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT="Reactive Autonomous Blackhole List"

CREATE TABLE IF NOT EXISTS `rabl-automatic` (
  `ip` char(43) NOT NULL COMMENT "The reported IP address or network",
  `reporter` char(43) NOT NULL COMMENT "The IP of the reporting user",
  `spam_count` int(11) default 0 COMMENT "The number of spam messages seen from this IP",
  `last_seen` timestamp COMMENT "Last time a spam message was seen from this IP by this user",
  PRIMARY KEY  (`ip`, `reporter`),
  KEY  (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT="Reactive Autonomous Blackhole List"
