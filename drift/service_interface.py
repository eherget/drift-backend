import requests

from drift.constants import AUTH_HEADER_NAME
from drift.exceptions import ServiceError


def get_key_from_headers(incoming_headers):
    """
    return auth key from header
    """
    return incoming_headers.get(AUTH_HEADER_NAME)


def _validate_service_response(response, logger):
    """
    Raise an exception if the response was not what we expected.
    """
    if response.status_code is not requests.codes.ok:
        logger.warn(
            "%s error received from service: %s" % (response.status_code, response.text)
        )
        raise ServiceError("Error received from backend service")


def _fetch_url(url, auth_header, logger, time_metric, exception_metric):
    """
    helper to make a single request
    """
    logger.debug("fetching %s" % url)
    with time_metric.time():
        with exception_metric.count_exceptions():
            response = requests.get(url, headers=auth_header)
    logger.debug("fetched %s" % url)
    _validate_service_response(response, logger)
    return response.json()


def fetch_data(url, auth_header, object_ids, logger, time_metric, exception_metric):
    """
    fetch objects based on ID in batches of 40 for given RESTful URL

    A batch size of 40 was chosen to fetch as many items per request as we
    can, but still keep some headroom in the URL length.
    """
    BATCH_SIZE = 40
    results = []
    object_ids_to_fetch = object_ids

    while len(object_ids_to_fetch) > 0:
        object_id_batch = object_ids_to_fetch[:BATCH_SIZE]
        response_json = _fetch_url(
            url % (",".join(object_id_batch)),
            auth_header,
            logger,
            time_metric,
            exception_metric,
        )
        results += response_json["results"]
        object_ids_to_fetch = object_ids_to_fetch[BATCH_SIZE:]

    return results
