from rest_framework.throttling import UserRateThrottle


class BorrowRateThrottle(UserRateThrottle):
    rate = "5/hour"
