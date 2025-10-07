import os
import threading
import logging
import time
from twisted.internet import reactor, threads
from cohen3 import server
from cohen3.backends.models.stores import BackendStore
from cohen3.backends.models.items import BackendItem
from coherence.upnp.core import DIDLLite

logger = logging.getLogger(__name__)

class MediaHubDLNAItem(BackendItem):
    """Represents a single media item from MediaHub's library for DLNA."""
    def __init__(self, parent_id, item_id, urlbase, path, title, mimetype, size, **kwargs):
        super().__init__(parent_id, item_id, urlbase, **kwargs)
        self.path = path
        self.title = title
        self.mimetype = mimetype
        self.size = size

        self.item.title = title
        self.item.res.append(DIDLLite.Resource(self.location, f'http-get:*:{mimetype}:*'))
        self.item.res[0].size = size

class MediaHubDLNAStore(BackendStore):
    """A Cohen3 backend store that exposes MediaHub's media library."""
    logCategory = 'mediahub_dlna_store'
    implements = ['MediaServer']

    def __init__(self, server, *args, **kwargs):
        BackendStore.__init__(self, server, *args, **kwargs)
        self.name = kwargs.get('name', 'MediaHub DLNA Server')
        self.media_root_path = kwargs.get('media_root_path', os.path.join(os.getcwd(), 'media'))
        self.items = {}
        self.update_id = 0
        logger.info(f"MediaHub DLNA Store initialized. Serving from: {self.media_root_path}")
        self.wmc_mapping = {'4': 0}

        # Initial scan of media files
        self.refresh_content()

    def refresh_content(self):
        """Scans the media_root_path and populates the DLNA store."""
        logger.info(f"Scanning media directory: {self.media_root_path}")
        self.items = {}
        self.update_id += 1
        idx = 1
        for root, _, files in os.walk(self.media_root_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Basic mimetype detection - could be improved
                mimetype = 'video/mpeg' # Default
                if file.endswith(('.mp4', '.mkv', '.avi', '.webm')):
                    mimetype = 'video/mp4'
                elif file.endswith(('.mp3', '.flac', '.aac', '.ogg')):
                    mimetype = 'audio/mpeg'
                elif file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    mimetype = 'image/jpeg'

                try:
                    size = os.path.getsize(file_path)
                except OSError:
                    size = 0

                item_id = str(idx)
                self.items[item_id] = MediaHubDLNAItem(
                    parent_id=0, item_id=item_id, urlbase=self.urlbase,
                    path=file_path, title=file, mimetype=mimetype, size=size
                )
                idx += 1
        logger.info(f"Finished scanning. Found {len(self.items)} media items.")

    def get_by_id(self, item_id):
        """Returns a media item by its ID."""
        return self.items.get(str(item_id))

    def get_children(self, parent_id, start=0, request_count=0):
        """Returns children of a given parent ID."""
        # For simplicity, we'll treat the root as the only container
        # and return all items directly.
        if str(parent_id) == '0': # Root container
            children = list(self.items.values())
            return children[start:start + request_count] if request_count else children
        return []

    def get_child_count(self, parent_id):
        """Returns the number of children for a given parent ID."""
        if str(parent_id) == '0':
            return len(self.items)
        return 0

class MediaHubDLNAServer:
    def __init__(self, media_path, port=8200):
        self.media_path = media_path
        self.port = port
        self.dlna_server = None
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            logger.info("DLNA server is already running.")
            return

        logger.info(f"Starting DLNA server on port {self.port} serving from {self.media_path}")
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()

    def _run_server(self):
        try:
            # Cohen3 requires Twisted reactor to run in the main thread or be explicitly started
            # We use threads.blockingCallFromThread to ensure reactor operations are safe
            threads.blockingCallFromThread(reactor.callFromThread, self._start_cohen_server)
            reactor.run(installSignalHandlers=0)
        except Exception as e:
            logger.error(f"Error running DLNA server: {e}")

    def _start_cohen_server(self):
        """Starts the Cohen3 UPnP server within the Twisted reactor thread."""
        config = {
            'name': 'MediaHub DLNA Server',
            'uuid': 'MediaHub-DLNA-Server-UUID',
            'plugins': [
                {
                    'plugin': 'backend:MediaHubDLNAStore',
                    'name': 'MediaHub Content',
                    'media_root_path': self.media_path
                }
            ]
        }
        self.dlna_server = server.UPnP(config)
        self.dlna_server.start()
        logger.info("Cohen3 UPnP server started successfully.")

    def stop(self):
        if self.dlna_server:
            logger.info("Stopping DLNA server.")
            threads.blockingCallFromThread(reactor.callFromThread, self.dlna_server.stop)
        if reactor.running:
            threads.blockingCallFromThread(reactor.callFromThread, reactor.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            logger.info("DLNA server thread stopped.")

# Example usage (for testing purposes)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_media_path = os.path.join(os.getcwd(), 'test_media')
    os.makedirs(test_media_path, exist_ok=True)
    with open(os.path.join(test_media_path, 'test_video.mp4'), 'w') as f:
        f.write('dummy video content')
    with open(os.path.join(test_media_path, 'test_audio.mp3'), 'w') as f:
        f.write('dummy audio content')

    dlna = MediaHubDLNAServer(test_media_path)
    dlna.start()
    print("DLNA server started in background. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dlna.stop()
        print("DLNA server stopped.")

