import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import CurrentUser

import boto3
from botocore.exceptions import ClientError
import io

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "static" / "uploads"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/uploads", tags=["uploads"])

# @router.get("", status_code=status.HTTP_200_OK)
# def upload_to_s3():
#     s3 = boto3.client(
#         "s3",
#         endpoint_url="http://localhost:4566",
#         region_name="us-east-1",
#         aws_access_key_id="test",
#         aws_secret_access_key="test"
#     )

#     # 1. Create bucket safely
#     try:
#         s3.create_bucket(Bucket="mealate")
#         print("Bucket created")
#     except ClientError as e:
#         if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
#             print("Bucket already exists, skipping...")
#         else:
#             raise  # re-raise unexpected errors

#     # 2. Upload file
#     local_path = "/Users/mac/Desktop/mealate_project/mealate_back/static/uploads/7a215a90ef1546389e3ea213f39eed9a.jpeg"
#     s3_key = "new_object"

#     s3.upload_file(local_path, "mealate", s3_key)
#     print(f"Uploaded: {s3_key}")

#     # 3. Download file — saves to disk, then read it
#     download_path = "/Users/mac/Desktop/downloaded_image.jpeg"
#     s3.download_file("mealate", s3_key, download_path)
#     print(f"Downloaded to: {download_path}")

# # 4. Read the downloaded file if needed
# with open(download_path, "rb") as f:
#     file_bytes = f.read()
#     print(f"File size: {len(file_bytes)} bytes")

# return file_bytes


# def upload_to_s3():
#     s3 = boto3.client(
#     "s3",
#     endpoint_url="http://localhost:4566",  # point to LocalStack
#     region_name="us-east-1",
#     aws_access_key_id="test",              # any fake value works
#     aws_secret_access_key="test"           # any fake value works
#     )

#     if s3.create_bucket(Bucket="mealate"):
#         print("Bucket Created")

#     s3.upload_file("/Users/mac/Desktop/mealate_project/mealate_back/static/uploads/7a215a90ef1546389e3ea213f39eed9a.jpeg", "mealate", "new_object")

#     print(s3.download_file('mealate', 'new_object', '/Users/mac/Desktop/mealate_project/mealate_back/static/uploads/7a215a90ef1546389e3ea213f39eed9a.jpeg'))


def upload_to_s3(
    file_bytes: bytes,
    content_type: str = "image/jpeg",
    bucket: str = "mealate",
    folder: str = "uploads",
):
    s3 = boto3.client(
        "s3",
    )
    extension = content_type.split("/")[-1]
    s3_key = f"{folder}/{uuid.uuid4().hex}.{extension}"
    if s3.upload_fileobj(
        io.BytesIO(file_bytes), bucket, s3_key, ExtraArgs={"ContentType": content_type}
    ):
        print("IMAGE UPLOADED")
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": s3_key}, ExpiresIn=3600
    )
    return url


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile, _: CurrentUser) -> dict[str, str]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, WebP and GIF images are accepted",
        )

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be smaller than 5 MB",
        )

    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        ext = "jpg"

    filename = f"{uuid.uuid4().hex}.{ext}"

    url = upload_to_s3(data, bucket="mealate")
    print("url: ", url)

    return {"url": url}
