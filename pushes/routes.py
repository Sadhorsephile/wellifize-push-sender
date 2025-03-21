from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from integrations import apns
from integrations import firebase as fb
from integrations.cache import LocalCacheRepository, RedisCacheRepository
from integrations.redis import connection as redis_con
from project_base.config import get_settings
from project_base.loggers import logger

from .authentication import authenticate_request
from .repositories import RedisTokenRepository
from .schemas import SendPushByTokenSchema, SendPushByUserIdSchema, TokenRequestSchema

settings = get_settings()
router = APIRouter()


@router.post('/fcm/add-token', status_code=status.HTTP_201_CREATED)
def add_fcm_token(auth: Annotated[None, Depends(authenticate_request)], data: TokenRequestSchema) -> None:
    """Save FCM token for the specified user."""
    if redis_con is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'No token storage was initialized')

    repo = RedisTokenRepository(redis_con, 'user:{user_id}:fcm-tokens')
    repo.add(data.user_id, data.token)


@router.post('/fcm/delete-token', status_code=status.HTTP_204_NO_CONTENT)
def delete_fcm_token(auth: Annotated[None, Depends(authenticate_request)], data: TokenRequestSchema) -> None:
    """Delete specified FCM token for the specified user."""
    if redis_con is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'No token storage was initialized')

    repo = RedisTokenRepository(redis_con, 'user:{user_id}:fcm-tokens')
    repo.delete(data.user_id, data.token)


@router.post('/fcm/send-by-user-id', status_code=status.HTTP_204_NO_CONTENT)
def send_fcm_push_by_user_id(
    auth: Annotated[None, Depends(authenticate_request)], data: SendPushByUserIdSchema
) -> None:
    """Send an FCM push notification by user_id."""
    if redis_con is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'No token storage was initialized')

    tokens_repo = RedisTokenRepository(redis_con, 'user:{user_id}:fcm-tokens')
    tokens = tokens_repo.get_all_by_user_id(data.user_id)

    cache_storage = RedisCacheRepository(redis_con) if redis_con is not None else LocalCacheRepository()
    firebase_service = fb.FireBase(cache_storage, logger)

    data_to_send = {'guid': data.guid, 'call_status': data.status, 'click_action': 'FLUTTER_NOTIFICATION_CLICK'}

    err_occured = False
    for token in tokens:
        try:
            firebase_service.send_message(fcm_token=token, title=None, message=None, extra_data=data_to_send)
        except (fb.FireBaseInvalidRequestError, fb.FireBaseFCMTokenNotFoundError):
            tokens_repo.delete(data.user_id, token)
        except fb.FireBaseTokenError:
            firebase_service.delete_access_token()
            firebase_service.send_message(fcm_token=token, title=None, message=None, extra_data=data_to_send)
        except fb.FireBaseServiceError:
            err_occured = True

    if err_occured:
        msg = 'An FCM error occured. Some pushes were not sent'
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg) from None


@router.post('/fcm/send-by-token', status_code=status.HTTP_204_NO_CONTENT)
def send_fcm_push_by_token(auth: Annotated[None, Depends(authenticate_request)], data: SendPushByTokenSchema) -> None:
    """Send an FCM push notification by token."""
    storage = RedisCacheRepository(redis_con) if redis_con is not None else LocalCacheRepository()
    firebase_service = fb.FireBase(storage, logger)

    data_to_send = {'guid': data.guid, 'call_status': data.status, 'click_action': 'FLUTTER_NOTIFICATION_CLICK'}

    try:
        firebase_service.send_message(fcm_token=data.token, title=None, message=None, extra_data=data_to_send)
    except fb.FireBaseFCMTokenNotFoundError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'FCM token is not registered') from None
    except fb.FireBaseTokenError:
        firebase_service.delete_access_token()
        firebase_service.send_message(fcm_token=data.token, title=None, message=None, extra_data=data_to_send)
    except fb.FireBaseInvalidRequestError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid FCM request') from None
    except fb.FireBaseServiceError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "FCM isn't available") from None


@router.post('/apns/add-token', status_code=status.HTTP_201_CREATED)
def add_apns_token(auth: Annotated[None, Depends(authenticate_request)], data: TokenRequestSchema) -> None:
    """Save APNS token for the specified user."""
    if redis_con is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'No token storage was initialized')

    repo = RedisTokenRepository(redis_con, 'user:{user_id}:apns-tokens')
    repo.add(data.user_id, data.token)


@router.post('/apns/delete-token', status_code=status.HTTP_204_NO_CONTENT)
def delete_apns_token(auth: Annotated[None, Depends(authenticate_request)], data: TokenRequestSchema) -> None:
    """Delete specified APNS token for the specified user."""
    if redis_con is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'No token storage was initialized')

    repo = RedisTokenRepository(redis_con, 'user:{user_id}:apns-tokens')
    repo.delete(data.user_id, data.token)


@router.post('/apns/send-by-user-id', status_code=status.HTTP_204_NO_CONTENT)
def send_apns_push_by_user_id(
    auth: Annotated[None, Depends(authenticate_request)], data: SendPushByUserIdSchema
) -> None:
    """Send an APNS push notification by user_id."""
    if redis_con is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'No token storage was initialized')

    tokens_repo = RedisTokenRepository(redis_con, 'user:{user_id}:apns-tokens')
    tokens = tokens_repo.get_all_by_user_id(data.user_id)

    cache_storage = RedisCacheRepository(redis_con) if redis_con is not None else LocalCacheRepository()
    apns_creds = apns.TokenCredentials(
        cache_storage, settings.APNS_AUTH_KEY, settings.APNS_AUTH_KEY_ID, settings.APNS_TEAM_ID
    )
    apns_client = apns.APNSClient(logger, apns_creds, use_sandbox=settings.APNS_USE_SANDBOX)

    payload = apns.Payload(badge=1, custom={'guid': data.guid}, content_available=True)

    err_occured = False
    for token in tokens:
        try:
            apns_client.send_notification(token, payload, topic='com.archetype.wellifize.dev.voip', expiration=0)
        except (apns.BadDeviceTokenError, apns.ExpiredTokenError):
            tokens_repo.delete(data.user_id, token)
        except apns.ExpiredProviderTokenError:
            apns_creds.delete_access_token()
            apns_client.send_notification(token, payload, topic='com.archetype.wellifize.dev.voip', expiration=0)
        except (apns.UnregisteredError, apns.TooManyRequestsError):
            pass
        except apns.APNSServiceError:
            err_occured = True

    if err_occured:
        msg = 'An APNS error occured. Some pushes were not sent'
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg) from None


@router.post('/apns/send-by-token', status_code=status.HTTP_204_NO_CONTENT)
def send_apns_push_by_token(auth: Annotated[None, Depends(authenticate_request)], data: SendPushByTokenSchema) -> None:
    """Send an APNS push notification by token."""
    cache_storage = RedisCacheRepository(redis_con) if redis_con is not None else LocalCacheRepository()
    apns_creds = apns.TokenCredentials(
        cache_storage, settings.APNS_AUTH_KEY, settings.APNS_AUTH_KEY_ID, settings.APNS_TEAM_ID
    )
    apns_client = apns.APNSClient(logger, apns_creds, use_sandbox=settings.APNS_USE_SANDBOX)

    payload = apns.Payload(badge=1, custom={'guid': data.guid}, content_available=True)

    try:
        apns_client.send_notification(data.token, payload, topic='com.archetype.wellifize.dev.voip', expiration=0)
    except apns.BadDeviceTokenError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'APNS error: BadDeviceToken') from None
    except apns.ExpiredProviderTokenError:
        apns_creds.delete_access_token()
        apns_client.send_notification(data.token, payload, topic='com.archetype.wellifize.dev.voip', expiration=0)
    except apns.ExpiredTokenError:
        raise HTTPException(status.HTTP_410_GONE, 'APNS error: ExpiredToken') from None
    except apns.UnregisteredError:
        raise HTTPException(status.HTTP_410_GONE, 'APNS error: Unregistered') from None
    except apns.TooManyRequestsError:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, 'APNS error: TooManyRequests') from None
    except apns.AnotherError as err:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, err.reason) from None
    except apns.APNSServiceError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "APNS isn't available") from None
