"""Parser for commandline arguments to the Action Module samples"""

import co3


class CafArgumentParser(co3.ArgumentParser):
    """Arguments for STOMP connection"""

    DEFAULT_PORT = 65001

    def __init__(self):
        super(CafArgumentParser, self).__init__(config_file="samples.config")

        default_stomp_host = self.getopt("resilient", "shost")
        default_stomp_port = self.getopt("resilient", "sport") or self.DEFAULT_PORT

        self.add_argument('--shost',
                          default=default_stomp_host,
                          help="STOMP host name (default is to use the value specified in --host)")

        self.add_argument('--sport',
                          type=int,
                          default=default_stomp_port,
                          help="STOMP port number")

        self.add_argument('destination',
                          nargs=1,
                          help="The destination to connect to (e.g. actions.201.test)")


    def parse_args(self, args=None, namespace=None):
        args = super(CafArgumentParser, self).parse_args(args, namespace)

        if not args.shost:
            args.shost = args.host

        return args
