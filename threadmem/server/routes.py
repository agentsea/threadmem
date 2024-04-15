from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from threadmem import RoleThread

from .models import (
    RoleThreadModel,
    CreateRoleThreadModel,
    V1UserProfile,
    RoleThreadsModel,
    PostMessageModel,
    UpdateRoleThreadModel,
    RoleModel,
    DeleteRoleModel,
)
from threadmem.auth.transport import get_current_user

router = APIRouter()


@router.post("/v1/rolethreads", response_model=RoleThreadModel)
async def create_role_thread(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)],
    data: CreateRoleThreadModel,
):
    thread = RoleThread(
        public=data.public,
        name=data.name,
        metadata=data.metadata,
        owner_id=current_user.email,
    )

    return thread.to_schema()


@router.get("/v1/rolethreads", response_model=RoleThreadsModel)
async def get_role_threads(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)]
):
    threads = RoleThread.find(owner_id=current_user.email)
    return RoleThreadsModel(threads=[thread.to_schema() for thread in threads])


@router.get("/v1/rolethreads/{id}", response_model=RoleThreadModel)
async def get_role_thread(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)], id: str
):
    print("\nfinding thread by id: ", id)
    threads = RoleThread.find(id=id, owner_id=current_user.email)
    print("\n!! found threads: ", threads)
    if not threads:
        print("\ndid not find thread by id: ", id)
        raise HTTPException(status_code=404, detail="Thread not found")
    print("\nfound thread by id: ", threads[0])
    return threads[0].to_schema()


@router.delete("/v1/rolethreads/{thread_id}")
async def delete_role_thread(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)], thread_id: str
):
    threads = RoleThread.find(id=thread_id, owner_id=current_user.email)
    if not threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    thread = threads[0]
    thread.delete()
    return {"message": "Thread deleted successfully"}


@router.post("/v1/rolethreads/{id}/msgs")
async def post_role_thread_msg(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)],
    id: str,
    data: PostMessageModel,
):
    print("\n posting message to thread: ", data)
    thread = RoleThread.find(id=id, owner_id=current_user.email)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    thread = thread[0]
    thread.post(data.role, data.msg, data.images)
    print("\nposted message to thread: ", thread.__dict__)
    return


@router.post("/v1/rolethreads/{id}/roles")
async def add_role_to_thread(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)],
    id: str,
    data: RoleModel,
):
    print("\nadding role to thread: ", data)
    thread = RoleThread.find(id=id, owner_id=current_user.email)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    thread = thread[0]
    thread.add_role(data)
    print("\nadded role to thread: ", thread.__dict__)
    return


@router.delete("/v1/rolethreads/{id}/roles")
async def remove_role_to_thread(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)],
    id: str,
    data: DeleteRoleModel,
):
    print("\nremoving role to thread: ", data)
    thread = RoleThread.find(id=id, owner_id=current_user.email)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    thread = thread[0]
    thread.remove_role(data.name)
    print("\nremoved role to thread: ", thread.__dict__)
    return


@router.put("/v1/rolethreads/{id}", response_model=RoleThreadModel)
async def update_role_thread(
    current_user: Annotated[V1UserProfile, Depends(get_current_user)],
    id: str,
    data: UpdateRoleThreadModel,
):
    print("\n updating thread with model: ", data)
    threads = RoleThread.find(id=id, owner_id=current_user.email)
    if not threads:
        raise HTTPException(status_code=404, detail="Task not found")
    thread = threads[0]

    print("\nfound thread: ", thread.__dict__)
    if data.name:
        thread.name = data.name
    if data.public:
        thread.public = data.public  # type: ignore
    if data.metadata:
        thread.metadata = data.metadata
    print("\nsaving task: ", thread.__dict__)
    thread.save()
    return thread.to_schema()
