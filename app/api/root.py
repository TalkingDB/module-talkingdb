from fastapi import APIRouter

router = APIRouter(tags=["Root"])


@router.get("/")
def get_org():
    return "Welcome to Module TalkingDB!"
