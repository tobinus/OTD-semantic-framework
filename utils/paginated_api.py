def fetch(
        requests_session,
        url,
        page_size,
        offset_param_name,
        limit_param_name,
        result_getter,
        count_getter,
        response_validator=None
):
    """
    Fetch records and number of records from a paginated API endpoint.

    This uses a generator, so the entire list is not downloaded at once.

    Args:
        requests_session: Session instance from the Requests library.
        url: Endpoint to make requests to. May already contain a query string.
        page_size: Number of records to request per page.
        offset_param_name: Name of query parameter which controls the number of
            records to skip before starting to return records from the endpoint.
            Used to communicate to the endpoint what "page" we want to get.
        limit_param_name: Name of query parameter which controls how many
            records should be returned from the endpoint per page. Used to
            communicate to the endpoint the desired "page size". Can be set to
            None, in which case the API's default behaviour is used.
        result_getter: Function which accepts a requests.Response, and returns
            an iterable of records. The records are then yielded, one record at
            a time. If no records could be found, it should return empty tuple.
        count_getter: Function which accepts a requests.Response, and returns
            the number of records that can be fetched from the given url.
        response_validator: Function which accepts a requests.Response, and
            does extra validity checks. If this returns anything but True, it
            will be made into a ValidationFailedError (with anything returned
            used as message). You may also raise an exception yourselves.

    Returns:
        Tuple of two items. The first item is a generator which yields records
        fetched from the API endpoint. The second item is the number of records,
        as returned by the count_getter function.
    """
    # Helper function for making requests
    def _do_request(offset):
        # Go via a dict, since we don't always want to set all parameters
        params = dict()

        # Always set offset (or else we cannot go through the pages)
        params[offset_param_name] = offset

        # Set page size, if we don't want to rely on the API's default behaviour
        if page_size is not None and limit_param_name is not None:
            params[limit_param_name] = page_size

        # Make request
        this_response = requests_session.get(
            url,
            params=params
        )

        # Check response validity, first by looking at status code
        this_response.raise_for_status()
        # Then use custom hook, if provided
        if response_validator:
            valid_response = response_validator(this_response)
            if valid_response is not True:
                if valid_response is False:
                    raise ValidationFailedError()
                else:
                    raise ValidationFailedError(valid_response)

        return this_response

    # Make our first request
    response = _do_request(offset=0)

    # Calculate the number of records available
    count = count_getter(response)

    def result_generator(initial_response):
        current_response = initial_response
        num_fetched = 0
        while num_fetched < count:
            # Don't make new request on first iteration
            if num_fetched != 0:
                current_response = _do_request(offset=num_fetched)

            # Go through the records from this page
            for record in result_getter(current_response):
                yield record
                num_fetched += 1
            # Catch situations where count is wrong, avoiding endless loop.
            # This could occur if for example one record is removed while we
            # loop over the pages.
            else:
                # Zero rows fetched by last request, abort
                raise RuntimeError(
                    f'Expected there to be {count} records, but list of '
                    f'records exhausted after fetching {num_fetched}.'
                )

    return result_generator(response), count


class ValidationFailedError(Exception):
    pass
