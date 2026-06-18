"""y402 exception hierarchy."""


class Y402Error(Exception):
    """Base for all y402 errors."""


class NetworkNotSupportedError(Y402Error):
    """The requested or offered network is not in the registry / not enabled."""


class NoUsableOfferError(Y402Error):
    """A 402 response carried no offer we can satisfy."""


class PolicyRefusedError(Y402Error):
    """The payment policy refused a payment."""


class KeystoreError(Y402Error):
    """Key could not be stored or loaded."""
