"""Parser for commandline arguments and config properties"""

import co3


class ParkOpts(dict):
    """A dictionary of the commandline options"""
    def __init__(self, config, dictionary):
        super(ParkOpts, self).__init__()
        self.config = config
        if dictionary is not None:
            self.update(dictionary)


class ParkArgumentParser(co3.ArgumentParser):
    """Helper to parse command line arguments."""

    DEFAULT_STOMP_PORT = 65001

    def __init__(self):
        super(ParkArgumentParser, self).__init__(config_file="park.config")

        default_stomp_port = self.getopt("resilient", "stomp_port") or self.DEFAULT_STOMP_PORT
        default_queue = self.getopt("resilient", "queue")

        default_park_url = self.getopt("park", "url")

        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")

        self.add_argument("--queue",
                          default=default_queue,
                          help="Message destination API name")

        self.add_argument("--park",
                          default=default_park_url,
                          help="Parks Service URL")

    def parse_args(self, args=None, namespace=None):
        args = super(ParkArgumentParser, self).parse_args(args, namespace)
        return ParkOpts(self.config, vars(args))
