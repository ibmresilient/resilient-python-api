"""Parser for commandline arguments and config properties"""

import co3


class CrossOrgOpts(dict):
    """A dictionary of the commandline options"""
    def __init__(self, config, dictionary):
        super(CrossOrgOpts, self).__init__()
        self.config = config
        if dictionary is not None:
            self.update(dictionary)


class CrossOrgArgumentParser(co3.ArgumentParser):
    """Helper to parse command line arguments."""

    DEFAULT_PORT = 443
    DEFAULT_STOMP_PORT = 65001

    def __init__(self):
        super(CrossOrgArgumentParser, self).__init__(config_file="crossorg.config")

        # Action Module connecion
        default_stomp_port = self.getopt("resilient", "stomp_port") or self.DEFAULT_STOMP_PORT
        default_queue = self.getopt("resilient", "queue")

        # Credentials for the "destination" org where incidents are created
        default_destemail = self.getopt("crossorg", "email")
        default_destpassword = self.getopt("crossorg", "password")
        default_desthost = self.getopt("crossorg", "host")
        default_destport = self.getopt("crossorg", "port")
        default_destorg = self.getopt("crossorg", "org")

        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")

        self.add_argument("--queue",
                          default=default_queue,
                          help="Message destination API name")

        self.add_argument("--destemail",
                          default=default_destemail,
                          help="The email address to use to authenticate to the destination Resilient server.")

        self.add_argument("--destpassword",
                          default=default_destpassword,
                          help="The password to use to authenticate to the destination Resilient server."
                               "If omitted, the you will be prompted.")

        self.add_argument("--desthost",
                          default=default_desthost,
                          help="Destination Resilient server host name")

        self.add_argument("--destport",
                          type=int,
                          default=default_destport,
                          help="Destination Resilient server REST API port number")

        self.add_argument("--destorg",
                          default=default_destorg,
                          required=default_destorg is None,
                          help="The name of the destination organization.")

    def parse_args(self, args=None, namespace=None):
        args = super(CrossOrgArgumentParser, self).parse_args(args, namespace)

        args.destemail = args.destemail or args.email
        args.destpassword = args.destpassword or args.password
        args.desthost = args.desthost or args.host
        args.destport = args.destport or args.port

        return CrossOrgOpts(self.config, vars(args))
