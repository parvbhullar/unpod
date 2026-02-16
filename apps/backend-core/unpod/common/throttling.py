from rest_framework.throttling import SimpleRateThrottle
from unpod.common.exception import APIException206
from unpod.common.validation import get_user_id


class UnpodRateThrottler(SimpleRateThrottle):
    scope = "user&anno"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            session_user, is_authenticated = get_user_id(request)
            if session_user is None:
                raise APIException206({"message": "session_user is required"})
            ident = session_user

        return self.cache_format % {"scope": self.scope, "ident": ident}

    def get_rate(self):
        return "10/day"

    def allow_request(self, request, view, return_bool=False):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return True if return_bool else self.throttle_success()
