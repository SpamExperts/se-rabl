#! /bin/sh

### BEGIN INIT INFO
# Provides:          rabl
# Required-Start:
# Required-Stop:
# Should-Start:
# Should-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start RABL daemon.
# Description:       Starts the RABL server daemon.
### END INIT INFO

PATH=/sbin:/bin:/usr/sbin:/usr/bin
DAEMON=/var/cache/se-rabl/rabl/rabl.py
PYTHONPATH=/var/cache/se-rabl/
PYTHONEXE=/var/cache/se-rabl-env/bin/python
NAME=rabl
DESC="RABL server"
PIDFILE="/var/run/rabl_server.pid"

test -x $DAEMON || exit 0
. /etc/default/rcS
start() {
    echo -n "Starting: "
    mkdir -p `dirname $PIDFILE`
    /usr/bin/env PYTHONPATH=$PYTHONPATH $PYTHONEXE $DAEMON 2>/dev/null && echo "${DAEMON##*/}."
}
stop() {
    echo -n "Stopping: "
    kill -15 `cat $PIDFILE` && echo "${DAEMON##*/}."
}
case "$1" in
 start)
    start
    ;;
 stop)
    stop
    ;;
 restart|force-reload)
    stop
    sleep 1
    start
    ;;
 *)
    N=/etc/init.d/$NAME
    echo "Usage: $N {start|stop|restart|force-reload}" >&2
    exit 1
    ;;
esac
exit 