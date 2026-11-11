import socket
import ssl
from logging import INFO, Formatter, getLogger
from queue import Empty
from tlssyslog.handlers import TLSSysLogHandler
from tlssyslog.worker import TCPLoggingThread
from ....config import config
from ....log import log


class VerifiedTCPLoggingThread(TCPLoggingThread):
    """TCPLoggingThread that verifies the server certificate and hostname.

    tlssyslog uses ssl.wrap_socket(), which cannot check the hostname and does
    not load the system CA store. This opens the connection with an SSLContext
    instead and keeps the rest of the tlssyslog behavior (queue, reconnects).
    """

    def __init__(self, address, timeout, queue, should_terminate, ssl_context):
        self.ssl_context = ssl_context
        super().__init__(address, timeout, queue, should_terminate, ssl_kwargs={})

    def _run_loop_inner(self):
        # Same as TCPLoggingThread._run_loop_inner, but the error messages do not
        # include the log message: it contains the WorkspaceOne token.
        try:
            message = self.queue.get(block=True, timeout=self.queue_block_timeout)
        except Empty:
            return
        try:
            if not getattr(self, 'socket', None):
                try:
                    self._open_socket()
                except Exception as err:  # pylint: disable=broad-except
                    log.error('Failed to open TLS connection to syslog collector %s: %s', self.address, err)
            if getattr(self, 'socket', None):
                try:
                    self._send_message(message)
                except Exception as err:  # pylint: disable=broad-except
                    log.error('Failed to send message to syslog collector %s: %s', self.address, err)
        finally:
            self.queue.task_done()

    def _open_socket(self):
        if getattr(self, 'socket', None):
            self._close_socket()
        self.socket = None
        sock = socket.create_connection(self.address, timeout=self.timeout)
        try:
            self.socket = self.ssl_context.wrap_socket(sock, server_hostname=self.address[0])
        except ssl.SSLError as err:
            sock.close()
            log.error('TLS handshake with syslog collector %s failed: %s', self.address, err)
            raise
        except Exception:
            sock.close()
            raise


class VerifiedTLSSysLogHandler(TLSSysLogHandler):
    """TLSSysLogHandler that sends through VerifiedTCPLoggingThread."""

    def __init__(self, address, ssl_context, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(address, **kwargs)

    def ensure_sender_thread_running(self):
        self.purge_forked_caches()
        if not self._sender_thread:
            self._sender_thread = VerifiedTCPLoggingThread(
                self.address, self.timeout, self.queue, self.thread_should_terminate, self.ssl_context)
            self._sender_thread.start()
        return self._sender_thread


def _ssl_context():
    context = ssl.create_default_context(cafile=config.get('workspaceone', 'syslog_ca_file') or None)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


serverlog = getLogger('ws1')
serverlog.setLevel(INFO)

tlsHandler = VerifiedTLSSysLogHandler(
    address=(config.get('workspaceone', 'syslog_host'), int(config.get('workspaceone', 'syslog_port'))),
    ssl_context=_ssl_context(),
)
tlsHandler.setLevel(INFO)

formatter = Formatter('%(asctime)s %(name)s %(threadName)-10s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
tlsHandler.setFormatter(formatter)

serverlog.addHandler(tlsHandler)
